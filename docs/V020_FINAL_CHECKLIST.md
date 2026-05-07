# v0.2.0 Final Release Checklist

Use this checklist before creating the final `v0.2.0` release.

## Code Quality

- [ ] `uv run python -m compileall src` passes
- [ ] `uv run pytest -q` passes
- [ ] `uv run deliveryops smoke-test --repo .` passes
- [ ] No unexpected files appear in `git status`
- [ ] `.deliveryops/` runtime files are ignored
- [ ] No secrets or local environment files are committed

## CLI

- [ ] `uv run deliveryops --help` is readable
- [ ] `uv run deliveryops continue --repo .` works with an initialized workflow
- [ ] `uv run deliveryops auto-continue --repo . --max-steps 3` stops before risky actions
- [ ] `uv run deliveryops analyze-repo --repo .` works
- [ ] `uv run deliveryops check-ci --repo .` handles missing PR/auth/checks cleanly

## Agent Architecture

- [ ] Agent prompt files exist
- [ ] Agent definitions exist
- [ ] Intake Agent fallback works
- [ ] Product Owner Agent fallback works
- [ ] Dev Agent patch generation remains approval-gated
- [ ] LLM/patch-generation actions are not auto-run by auto-continue

## Workflow Architecture

- [ ] CLI commands are modularized
- [ ] Application services are used for selected workflows
- [ ] Light adapters exist for external process boundaries
- [ ] `FeatureDeliveryWorkflow` provides the central workflow decision boundary
- [ ] `continue` uses workflow service/orchestrator
- [ ] `auto-continue` uses workflow service/orchestrator

## GitHub / CI

- [ ] GitHub CLI missing/auth errors are readable
- [ ] Missing PR state is handled
- [ ] No-checks state is handled
- [ ] Pending checks are handled
- [ ] Failed checks are handled
- [ ] JSON-based PR checks parsing is tested

## Repository Analysis

- [ ] Stack detection works
- [ ] Source/test/doc/config classification works
- [ ] Likely file scoring works
- [ ] Risky file detection works
- [ ] Source-to-test mapping works

## Documentation

- [ ] README explains v0.2 architecture direction
- [ ] `docs/V020_AGENT_ARCHITECTURE.md` is accurate
- [ ] `docs/KNOWN_LIMITATIONS.md` is current
- [ ] `docs/WORKFLOW_OVERVIEW.md` mentions the orchestrator
- [ ] `docs/V020_RELEASE_NOTES.md` is ready

## Release

- [ ] `v0.2.0-rc4` has been reviewed
- [ ] Final tag `v0.2.0` is created from `main`
- [ ] GitHub Release `v0.2.0` is created
