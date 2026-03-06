# Process Lifecycle Tracking

Use `ProcessSupervisor` in [swarm_supervisor.py](/Users/rlozano/repos/simpleagent/swarm_supervisor.py) as the lifecycle source of truth.

## What It Tracks
- `registered`
- `spawned`
- `process_started`
- `heartbeat`
- `process_error`
- `process_exiting`
- `process_died`
- `process_restarting`
- `restart_skipped`
- `heartbeat_timeout`
- `process_shutdown_complete`
- `process_killed`
- `worker_progress` (runtime stage/progress events)
- `worker_error` (normalized runtime errors with `error_type` and context)

Events are appended to `docs/process-events.jsonl`.

## Worker Function Contract
Worker target signature:

```python
def worker(stop_event, event_queue, *args, **kwargs):
    # stop_event is set on shutdown/restart
    # event_queue can be used for worker-specific progress events
    ...
```

## Minimal Example

```python
from swarm_supervisor import ProcessSupervisor, WorkerSpec, emit_event
import time

def planner_worker(stop_event, event_queue):
    while not stop_event.is_set():
        emit_event(event_queue, "worker_progress", agent_id="planner-1", role="planner", msg="planning")
        time.sleep(1)

if __name__ == "__main__":
    sup = ProcessSupervisor(
        heartbeat_timeout_sec=10,
        shutdown_timeout_sec=5,
        event_log_path="docs/process-events.jsonl",
    )
    sup.register(WorkerSpec(agent_id="planner-1", role="planner", target=planner_worker, max_restarts=2))
    sup.run()
```

## Operational Guidance
- Keep one supervisor process.
- Do not let workers write directly to shared state.
- Keep lifecycle logs append-only.
- Use `agent_id` as the stable identity, not `pid`.
