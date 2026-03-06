# Swarm Use Cases and Demos

This file contains practical, high-value demos for:

```bash
python3 lm --swarm --tui --endpoint ollama --model granite4:7b-a1b-h --swarm-workers 3 --swarm-max-reviews 3 --tool-timeout 90 --output-format markdown "..."
```

## Full Parameter Baseline

```bash
python3 lm --swarm --tui --endpoint ollama --model granite4:7b-a1b-h --swarm-workers 3 --swarm-max-reviews 3 --tool-timeout 90 --output-format markdown "your goal here"
```

Use this as the default shape for all swarm demos.

```bash
BASE="python3 lm --swarm --tui --endpoint ollama --model granite4:7b-a1b-h --swarm-workers 3 --swarm-max-reviews 3 --tool-timeout 90 --output-format markdown"
```

## 1) Repo Reliability Audit

```bash
$BASE "Audit this repo for reliability issues. Identify top 5 failure modes, impact, and concrete fixes with priorities."
```

Best for:
- Stabilizing early-stage systems.
- Building a hardening backlog.

## 2) Release Readiness Review

```bash
$BASE "Create a release-readiness checklist for this project: tests, observability, error handling, docs, deployment risks. Mark blockers vs nice-to-have."
```

Best for:
- Pre-release quality gates.
- Team handoff checklists.

## 3) Architecture v2 Proposal

```bash
$BASE "Review current swarm architecture and propose a v2 design with task dependencies, retries, confidence scoring, and migration steps."
```

Best for:
- Planning next architecture iteration.
- Making roadmap decisions.

## 4) Test Strategy Generation

```bash
$BASE "Generate a testing strategy for this codebase across unit, integration, and failure-injection tests. Provide a first 10-test implementation plan."
```

Best for:
- Turning quality goals into executable test plans.

## 5) Docs vs Code Drift Detection

```bash
$BASE "Find inconsistencies between implementation and docs in this repo. List mismatches and draft exact documentation updates."
```

Best for:
- Keeping docs trustworthy.
- Reducing onboarding confusion.

## 6) Production Hardening Plan

```bash
$BASE "Propose a production hardening plan for this agent: supervision, crash recovery, logging, metrics, and graceful shutdown standards."
```

Best for:
- Defining operational maturity requirements.

## 7) CLI UX Improvement Pass

```bash
$BASE "Analyze lm CLI UX and propose improvements to flags, defaults, and error messages with backward-compatible changes."
```

Best for:
- Improving local developer experience.

## 8) Performance Benchmark Design

```bash
$BASE "Design a minimal benchmark suite for this agent system: latency, task success rate, retry rate, and run-to-run variance. Include measurement method."
```

Best for:
- Tracking improvements over time.
- Preventing regressions.

## 9) Security and Safety Review

```bash
$BASE "Review this repo for security and safety risks including unsafe shell usage, unvalidated inputs, and error leakage. Provide prioritized remediations."
```

Best for:
- Baseline security posture review.

## 10) Incident Preparedness

```bash
$BASE "Create an incident response runbook for this project with detection signals, triage flow, rollback plan, and postmortem template."
```

Best for:
- Ops readiness before production rollout.

## Tips
- Keep prompts outcome-oriented: ask for ranked findings and concrete next actions.
- Use `--tui` for live process/heartbeat/reasoning/event visibility while tuning runs.
- Increase `--swarm-max-reviews` when prompts are broad or ambiguous.

## API-Ready Output

```bash
python3 lm --swarm --endpoint ollama --model granite4:7b-a1b-h --swarm-workers 2 --swarm-max-reviews 3 --tool-timeout 90 --output-format json "Audit this repo for reliability issues. Identify top 5 failure modes and prioritized fixes."
```

Use this mode when piping output into another service or storing structured run artifacts.

## TUI View

```bash
python3 lm --swarm --tui --endpoint ollama --model granite4:7b-a1b-h --swarm-workers 3 --swarm-max-reviews 3 --tool-timeout 90 --output-format markdown "Audit this repo for reliability issues. Identify top 5 failure modes and prioritized fixes."
```

Use this mode when you want live process/heartbeat/event visibility with keyboard shortcuts.
