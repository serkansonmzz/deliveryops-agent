# DeliveryOps Agent

DeliveryOps Agent is a CLI-first, approval-gated delivery workflow for existing GitHub repositories.

It helps turn a feature request into a structured delivery flow:

```text
request
→ GitHub issue
→ feature branch
→ architecture review
→ implementation plan
→ patch
→ approval
→ apply
→ tests
→ readiness check
→ commit
→ push
→ draft PR
→ final report
```

## MVP Status

DeliveryOps Agent is currently in `v0.1.0-rc1` final polish and release preparation for `v0.1.0`.

## What DeliveryOps Agent Does

DeliveryOps Agent helps turn a feature request into a GitHub-based delivery workflow.

It can:

- create a GitHub issue
- create a feature branch
- generate architecture review notes
- generate an implementation plan
- generate and validate patches
- require approval before applying patches
- detect and run safe tests
- analyze test failures
- generate commit messages
- require approval before commit, push, and draft PR
- open draft pull requests
- check GitHub CI status
- produce final delivery reports
- resume workflows from local state

## What It Does Not Do

DeliveryOps Agent does not:

- merge pull requests automatically
- deploy to production
- modify secrets
- run arbitrary shell commands
- bypass approval gates for risky actions
- replace human engineering review

## Installation

```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync
```

## Environment

Set up the required environment before running GitHub-backed or agent-backed flows:

```bash
export OPENAI_API_KEY=your_openai_api_key
export GITHUB_TOKEN=your_github_token
gh auth login
```

Notes:

- `OPENAI_API_KEY` is required for Agno/OpenAI-backed patch generation.
- `GITHUB_TOKEN` may be useful for GitHub access, but the workflow primarily expects an authenticated `gh` CLI session.
- `gh auth login` is required for issue creation, draft PR creation, progress comments, and CI checks.

## Core Workflow

The core DeliveryOps workflow is:

```text
request
→ inspect repository
→ initialize workspace
→ create GitHub issue
→ create feature branch
→ architecture review
→ implementation plan
→ generate patch
→ approval
→ apply patch
→ detect tests
→ run tests
→ readiness check
→ generate commit message
→ approval
→ commit
→ approval
→ push
→ approval
→ open draft PR
→ check CI
→ comment progress
→ final report
```

## Core Commands

- `deliveryops run --repo . --github-owner YOUR_USER --github-repo YOUR_REPO --request "..."` starts a full delivery workflow.
- `deliveryops continue --repo .` shows the next recommended workflow step.
- `deliveryops approval-status --repo .` shows the current pending approval request.
- `deliveryops apply-patch --repo .` applies an already approved patch.
- `deliveryops detect-tests --repo .` detects a safe test command.
- `deliveryops run-tests --repo .` runs the detected allowlisted test command.
- `deliveryops readiness-check --repo .` evaluates workflow readiness before commit, push, or PR.
- `deliveryops generate-commit-message --repo .` generates a conventional commit candidate.
- `deliveryops commit --repo .` creates an approved Git commit.
- `deliveryops push --repo .` pushes the current feature branch after approval.
- `deliveryops open-draft-pr --repo .` opens an approved draft pull request.
- `deliveryops check-ci --repo .` reads GitHub PR checks and records CI state.
- `deliveryops final-report --repo .` writes the final delivery report.
- `deliveryops smoke-test --repo .` runs a local end-to-end smoke test.
- `deliveryops auto-continue --repo .` runs only safe local workflow steps until the next approval gate.

## Approval Model

DeliveryOps is autonomous only where it is safe.

Approval is required for:

- applying patches
- creating commits
- pushing branches
- opening draft pull requests
- other state-changing or external write actions

Risky actions are surfaced through approval requests that include:

- action name
- risk level
- affected files
- exact command
- expected result
- rollback note
- active policy profile

## Policy Profiles

DeliveryOps supports policy profiles for different risk environments:

```bash
deliveryops set-policy-profile --repo . --profile personal_repo
deliveryops policy-status --repo . --action git_push
```

Available profiles:

- `sandbox`: local experimentation and smoke testing
- `personal_repo`: default MVP behavior for personal repositories
- `production_repo`: stricter readiness and testing requirements before push or draft PR actions

## Testing

Run the unit test suite:

```bash
uv run pytest -q
```

DeliveryOps only runs allowlisted test commands such as:

- `uv run pytest -q`
- `python -m pytest -q`
- `pytest -q`
- `npm test`
- `pnpm test`
- `yarn test`

## Smoke Test

Run a local end-to-end smoke test without touching a real GitHub repository:

```bash
uv run deliveryops smoke-test --repo .
```

## CI Watcher

Check GitHub PR checks / GitHub Actions status:

```bash
uv run deliveryops check-ci --repo .
```

This command reads GitHub PR check status with GitHub CLI and updates `.deliveryops/state.json` plus `.deliveryops/DELIVERY.md`.

## Controlled Fix Patch Loop

Generate a controlled fix patch after failed tests or CI checks:

```bash
uv run deliveryops generate-fix-patch --repo .
```

The command uses failure analysis to ask the Dev Agent for a minimal fix patch. The patch is still sanitized, validated, and requires `apply_patch` approval before being applied.

## Docs

- `docs/MVP_RELEASE_CANDIDATE.md`
- `docs/WORKFLOW_OVERVIEW.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/DEMO_SCRIPT.md`
- `docs/MANUAL_E2E_TEST.md`
- `docs/V010_FINAL_CHECKLIST.md`
- `docs/MVP_RELEASE_NOTES.md`

## Known Limitations

See `docs/KNOWN_LIMITATIONS.md` for the current MVP boundaries and safety notes.

## Release Status

Current release preparation flow:

```text
v0.1.0-rc1
→ final polish
→ manual validation prep
→ docs cleanup
→ v0.1.0 final release
```
