# Swarm Mode

`lm` now supports a process-based swarm mode with planner/worker stubs.

## Run

```bash
python3 lm --swarm --swarm-workers 3 -d "summarize the repo and suggest next steps"
```

```bash
python3 lm --swarm --tui --endpoint ollama --model granite4:7b-a1b-h --swarm-workers 3 --swarm-max-reviews 3 --task-retries 3 "summarize the repo and suggest next steps"
```

```bash
python3 lm --swarm --web --web-port 8765 --endpoint ollama --model granite4:7b-a1b-h --swarm-workers 3 --swarm-max-reviews 3 "summarize the repo and suggest next steps"
```

## Behavior
- Starts `planner-1`, `worker-N`, `critic-1`, and `synthesizer-1` processes.
- Planner breaks your prompt into up to 5 tasks.
- Workers consume tasks concurrently and return per-task results.
- Worker tasks run through a tool-calling loop, so file-creation/update prompts can execute real writes via tools (for example `write_file`).
- Critic evaluates the collected worker results and gates final output (`pass|fail`).
- On critic `fail`, critic can return `follow_up_tasks`; coordinator enqueues them and reruns workers, then re-reviews.
- Synthesizer builds one cohesive final response from critic-approved outputs.
- Planner/worker/critic/synthesizer model calls use hard per-call timeouts based on `--tool-timeout`.
- If synthesizer times out/fails after critic `pass`, coordinator falls back to merged task outputs.
- Coordinator prints lifecycle events in debug mode.
- Lifecycle events are persisted to `docs/process-events.jsonl`.
- `--web` serves a local dashboard at `http://127.0.0.1:<--web-port>` with live process, token, reasoning, and event views.

## Accuracy-Oriented Prompt Guidance
- Keep each role narrow:
  planner emits task JSON, workers gather evidence, critic checks support and gaps, synthesizer merges only approved claims.
- Preserve `Please explain yourself`, but scope it to reasoning only:
  `Please explain yourself in your reasoning process, but do not include that reasoning in the final output.`
- For planner accuracy, prefer `1` task when the request is simple and split only when parallel work improves verification quality.
- For worker accuracy, require reading files and running checks before making code claims; explicitly separate observed facts, inferences, and unknowns.
- For critic accuracy, use an evidence checklist instead of open-ended judgment:
  verify support from code inspection, command output, test results, or explicit user input; fail when evidence is thin.
- For synthesizer accuracy, prohibit adding new facts, preserve uncertainty, and report conflicts instead of guessing.
- Avoid combining `Return only JSON` with output-facing prose requests. If you keep `Please explain yourself`, direct that reasoning away from the final structured payload.

## Flags
- `--swarm`: use swarm coordinator instead of the single agent loop.
- `--tui`: show grouped dashboard with process table, heartbeat table, and recent event stream (requires `rich`).
  Includes a `Reasoning` panel with per-agent reasoning summaries emitted at key steps.
  Shows live token usage totals in the header and per-agent token totals in the process table.
  Header also shows request count (successful model calls) and worker error count.
  Keybindings: `Tab` cycles views, `r` reasoning, `e` events, `p` processes, `d` dashboard, `q` quit.
- `--web`: start a lightweight local HTTP dashboard for swarm runtime visibility.
- `--web-port`: port for the `--web` server (default `8765`).
  `--web` does not require `rich`; unlike `--tui`, it uses only Python stdlib HTTP serving.
- `--endpoint`: inference backend label (currently only `ollama` is implemented).
- `--model`: model name used for all swarm stages.
- `--swarm-workers`: number of worker processes (default `2`).
- `--swarm-max-reviews`: max critic review rounds with follow-up retries (default `2`).
- `--task-retries`: max retries for the same swarm task after a worker timeout/error (default `3`).
- `--output-format`: `markdown` (human-readable) or `json` (API-friendly).
- `--debug` / `-d`: print lifecycle + per-step trace.
- `--max-steps`: loop bound for non-swarm mode. Swarm progression is primarily controlled by `--swarm-max-reviews` and timeouts.
- `--tool-timeout`: hard timeout (seconds) for planner/worker/critic/synth model calls and related wait windows; also used to derive swarm heartbeat timeout.

## Current Scope
This is a scaffold to iterate from:
- single planner
- worker pool
- task queue with per-task output collation
- critic gate before final output
- synthesizer stage for final response assembly
- critic-driven follow-up retry loop

Next step is dependency-aware task scheduling and per-task confidence scoring.
