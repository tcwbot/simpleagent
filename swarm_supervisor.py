import json
import multiprocessing as mp
import os
import queue
import signal
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Thread
from typing import Any, Callable, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def emit_event(event_queue: mp.Queue, event_type: str, **fields: Any) -> None:
    payload = {"ts": utc_now_iso(), "event": event_type, **fields}
    event_queue.put(payload)


def _heartbeat_loop(
    event_queue: mp.Queue,
    stop_event: mp.Event,
    agent_id: str,
    role: str,
    interval_sec: int,
) -> None:
    while not stop_event.is_set():
        emit_event(event_queue, "heartbeat", agent_id=agent_id, role=role)
        time.sleep(interval_sec)


def _worker_entry(
    agent_id: str,
    role: str,
    target: Callable[..., Any],
    stop_event: mp.Event,
    event_queue: mp.Queue,
    heartbeat_sec: int,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> None:
    emit_event(event_queue, "process_started", agent_id=agent_id, role=role, pid=os.getpid())

    hb = Thread(
        target=_heartbeat_loop,
        args=(event_queue, stop_event, agent_id, role, heartbeat_sec),
        daemon=True,
    )
    hb.start()

    exit_code = 0
    reason = "completed"
    try:
        target(stop_event, event_queue, *args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        exit_code = 1
        reason = f"error: {exc}"
        emit_event(
            event_queue,
            "process_error",
            agent_id=agent_id,
            role=role,
            pid=os.getpid(),
            details=str(exc),
        )
    finally:
        stop_event.set()
        emit_event(
            event_queue,
            "process_exiting",
            agent_id=agent_id,
            role=role,
            pid=os.getpid(),
            exit_code=exit_code,
            reason=reason,
        )


@dataclass
class WorkerSpec:
    agent_id: str
    role: str
    target: Callable[..., Any]
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    max_restarts: int = 1
    heartbeat_sec: int = 2


@dataclass
class WorkerState:
    spec: WorkerSpec
    process: Optional[mp.Process] = None
    stop_event: Optional[Any] = None
    pid: Optional[int] = None
    state: str = "registered"
    started_at: Optional[float] = None
    last_heartbeat: Optional[float] = None
    restarts: int = 0


class ProcessSupervisor:
    def __init__(
        self,
        heartbeat_timeout_sec: int = 10,
        shutdown_timeout_sec: int = 5,
        event_log_path: str = "docs/process-events.jsonl",
    ) -> None:
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self.shutdown_timeout_sec = shutdown_timeout_sec
        self.event_log_path = event_log_path
        self.event_queue: mp.Queue = mp.Queue()
        self.workers: dict[str, WorkerState] = {}
        self._stopping = False
        self._ensure_event_log_dir()

    def _ensure_event_log_dir(self) -> None:
        log_dir = os.path.dirname(self.event_log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

    def _append_event(self, event: dict[str, Any]) -> None:
        with open(self.event_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=True) + "\n")

    def register(self, spec: WorkerSpec) -> None:
        self.workers[spec.agent_id] = WorkerState(spec=spec)
        self._append_event({"ts": utc_now_iso(), "event": "registered", "agent_id": spec.agent_id, "role": spec.role})

    def start(self, agent_id: str) -> None:
        worker = self.workers[agent_id]
        stop_event = mp.Event()
        proc = mp.Process(
            target=_worker_entry,
            args=(
                worker.spec.agent_id,
                worker.spec.role,
                worker.spec.target,
                stop_event,
                self.event_queue,
                worker.spec.heartbeat_sec,
                worker.spec.args,
                worker.spec.kwargs,
            ),
            daemon=False,
        )
        proc.start()
        worker.process = proc
        worker.stop_event = stop_event
        worker.pid = proc.pid
        worker.state = "running"
        worker.started_at = time.time()
        worker.last_heartbeat = time.time()
        self._append_event(
            {
                "ts": utc_now_iso(),
                "event": "spawned",
                "agent_id": worker.spec.agent_id,
                "role": worker.spec.role,
                "pid": proc.pid,
                "restart_count": worker.restarts,
            }
        )

    def start_all(self) -> None:
        for agent_id in self.workers:
            self.start(agent_id)

    def _restart(self, agent_id: str, reason: str) -> None:
        worker = self.workers[agent_id]
        if worker.restarts >= worker.spec.max_restarts:
            worker.state = "failed"
            self._append_event(
                {
                    "ts": utc_now_iso(),
                    "event": "restart_skipped",
                    "agent_id": worker.spec.agent_id,
                    "role": worker.spec.role,
                    "reason": reason,
                    "max_restarts": worker.spec.max_restarts,
                }
            )
            return

        worker.restarts += 1
        self._append_event(
            {
                "ts": utc_now_iso(),
                "event": "process_restarting",
                "agent_id": worker.spec.agent_id,
                "role": worker.spec.role,
                "reason": reason,
                "restart_count": worker.restarts,
            }
        )
        self.start(agent_id)

    def drain_events(self) -> list[dict[str, Any]]:
        drained: list[dict[str, Any]] = []
        while True:
            try:
                event = self.event_queue.get_nowait()
            except queue.Empty:
                break

            agent_id = event.get("agent_id")
            worker = self.workers.get(agent_id)
            if worker and event.get("event") == "heartbeat":
                worker.last_heartbeat = time.time()
            if worker and event.get("event") == "process_exiting":
                worker.state = "stopped"
            self._append_event(event)
            drained.append(event)
        return drained

    def check_workers(self) -> None:
        now = time.time()
        for agent_id, worker in self.workers.items():
            if worker.state not in {"running", "stopped"}:
                continue
            proc = worker.process
            if not proc:
                continue

            if not proc.is_alive() and worker.state == "running":
                worker.state = "exited"
                self._append_event(
                    {
                        "ts": utc_now_iso(),
                        "event": "process_died",
                        "agent_id": worker.spec.agent_id,
                        "role": worker.spec.role,
                        "pid": worker.pid,
                        "exit_code": proc.exitcode,
                    }
                )
                if not self._stopping:
                    self._restart(agent_id, "process_died")
                continue

            if worker.last_heartbeat and (now - worker.last_heartbeat) > self.heartbeat_timeout_sec:
                self._append_event(
                    {
                        "ts": utc_now_iso(),
                        "event": "heartbeat_timeout",
                        "agent_id": worker.spec.agent_id,
                        "role": worker.spec.role,
                        "pid": worker.pid,
                        "seconds_since_heartbeat": round(now - worker.last_heartbeat, 2),
                    }
                )
                if worker.stop_event:
                    worker.stop_event.set()
                proc.join(timeout=self.shutdown_timeout_sec)
                if proc.is_alive():
                    proc.terminate()
                    proc.join(timeout=1)
                worker.state = "timed_out"
                if not self._stopping:
                    self._restart(agent_id, "heartbeat_timeout")

    def shutdown(self) -> None:
        self._stopping = True
        for worker in self.workers.values():
            if worker.stop_event:
                worker.stop_event.set()

        deadline = time.time() + self.shutdown_timeout_sec
        for worker in self.workers.values():
            proc = worker.process
            if not proc:
                continue
            remaining = max(0.0, deadline - time.time())
            proc.join(timeout=remaining)
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=1)
                self._append_event(
                    {
                        "ts": utc_now_iso(),
                        "event": "process_killed",
                        "agent_id": worker.spec.agent_id,
                        "role": worker.spec.role,
                        "pid": worker.pid,
                        "reason": "shutdown_timeout",
                    }
                )
            else:
                self._append_event(
                    {
                        "ts": utc_now_iso(),
                        "event": "process_shutdown_complete",
                        "agent_id": worker.spec.agent_id,
                        "role": worker.spec.role,
                        "pid": worker.pid,
                    }
                )
            worker.state = "stopped"

    def run(self, poll_interval_sec: float = 0.5) -> None:
        def _handle_signal(_signum: int, _frame: Any) -> None:
            self.shutdown()
            raise SystemExit(0)

        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)

        self.start_all()
        while True:
            self.drain_events()
            self.check_workers()
            time.sleep(poll_interval_sec)
