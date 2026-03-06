# Swarm Architecture (Process-Based)

This project should start with a process-based swarm and a single coordinator.

## Roles
- `planner`: convert user goal into task list.
- `worker`: execute tool-bound tasks.
- `critic`: check evidence and identify gaps.
- `synthesizer`: produce final response when checks pass.

## Shared State (Blackboard)
Use one state object persisted by the coordinator:
- `goal`
- `tasks`: queued/running/done
- `artifacts`: tool outputs and summaries
- `decisions`
- `errors`
- `status`: `running|done|failed`

Only the coordinator mutates global state; workers return structured updates.

## Message Contracts (Current)
- Worker result:
  - `task_id`
  - `status`: `done|error`
  - `output`
  - `agent_id`
- Critic review:
  - `status`: `pass|fail`
  - `feedback`
  - `summary`
  - `follow_up_tasks`
  - `schema_invalid`
  - `request_id`
- Synthesizer result:
  - `status`: `ok|error`
  - `final_answer`
  - `details`
  - `request_id`

## Scheduling
Per round:
1. pick next runnable task
2. select role
3. run one worker step
4. validate JSON contract
5. update state
6. hand to critic when needed

Stop when:
- `status=done`, or
- max rounds reached, or
- repeated failure threshold reached.

## Reliability Defaults (Current)
- non-swarm max steps: `12` (`--max-steps`)
- swarm max review rounds: `2` (`--swarm-max-reviews`)
- model/operation timeout: `20s` (`--tool-timeout`)
- swarm heartbeat timeout: `max(--tool-timeout, 5)` (default `20s`)
- per-worker restart budget: `1`
