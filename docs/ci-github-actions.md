# CI with GitHub Actions

This repo includes a lightweight CI workflow:

- File: `.github/workflows/ci.yml`
- Triggers:
  - `push` to `main`/`master`
  - `pull_request`
  - `workflow_dispatch` (manual run)
- Current checks:
  - `python -m unittest -v tests/test_swarm_contracts.py`

## Enable/Disable

You can toggle CI in GitHub:
- Repository Settings -> Actions (enable/disable Actions globally), or
- Actions tab -> select workflow -> Disable/Enable workflow.

## Cost Notes

- Public repos: typically free on GitHub-hosted runners.
- Private repos: usage depends on your included minutes and plan.

This workflow is intentionally small to minimize runtime/minutes.
