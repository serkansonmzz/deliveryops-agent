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

## v0.2.0 Direction

After the v0.1.0 MVP release, DeliveryOps Agent will deepen the agent architecture.

The next architecture layer focuses on:

- formal agent prompt files
- agent definitions
- structured outputs per agent
- Agno agent factory
- central feature delivery workflow orchestration

See:

- `docs/V020_AGENT_ARCHITECTURE.md`

## Internal CLI Organization

DeliveryOps keeps the public CLI command names stable, but internally groups command handlers by responsibility:

- workflow commands
- approval commands
- patch commands
- test commands
- Git/GitHub delivery commands
- release commands
- policy commands
- agent commands

The CLI entrypoint remains `app.main:app`.

## Application Service Layer

DeliveryOps keeps CLI handlers thin by moving workflow use-case logic into application services.

The intended internal flow is:

```text
CLI command
→ application service
→ tools / policies / agents
→ state.json + DELIVERY.md
```

This keeps the public CLI stable while making workflow behavior easier to test and evolve.

## Light Ports / Adapters Boundary

DeliveryOps keeps external process calls behind lightweight adapters.

Examples:

- Git CLI adapter
- GitHub CLI adapter
- Test runner adapter
- Process adapter

The goal is to keep workflow and service logic independent from direct subprocess calls where practical, without introducing heavy framework-level architecture.

## Intake and Product Owner Agents

DeliveryOps uses an Intake Agent and a Product Owner Agent to structure raw feature requests before creating GitHub issues.

The flow is:

```text
raw request
→ FeatureRequest
→ IssueSpec
→ GitHub issue
```

If an LLM is unavailable or returns unusable output, DeliveryOps falls back to deterministic issue generation so the workflow can continue.

## Repository Analysis

Analyze repository structure and enrich DeliveryOps state:

```bash
deliveryops analyze-repo --repo .
```

The repository analysis step detects stack signals, source files, test files, documentation files, risky files, and likely files related to the current request.

## v0.2.0 Architecture Update

DeliveryOps Agent v0.2.0 deepens the internal architecture around agent roles, services, adapters, and workflow orchestration.

Key additions:

- modular CLI command organization
- application service layer
- lightweight ports/adapters boundary
- formal agent definitions and prompt files
- Intake + Product Owner agent integration
- repository analysis
- hardened GitHub / CI integration
- `FeatureDeliveryWorkflow` orchestration boundary
- safer auto-continue behavior

DeliveryOps keeps a strict safety boundary:

```text
LLM agents reason and propose.
Deterministic tools execute and enforce.
Approval gates protect risky actions.
```

See:

- `docs/V020_AGENT_ARCHITECTURE.md`
- `docs/V020_RELEASE_NOTES.md`
- `docs/V020_FINAL_CHECKLIST.md`

## GitHub / CI Hardening

DeliveryOps reads GitHub PR check status through GitHub CLI.

The CI watcher handles:

- missing GitHub CLI
- missing authentication
- missing pull request
- no checks
- pending checks
- failed checks
- passed checks

Use:

```bash
deliveryops check-ci --repo .
```

## Feature Delivery Workflow Orchestrator

DeliveryOps now has a central workflow orchestration boundary:

```text
CLI
→ workflow service
→ FeatureDeliveryWorkflow
→ deterministic workflow decision tools
→ state.json + DELIVERY.md
```

The orchestrator keeps workflow step decisions in one place and prepares the project for deeper Agno-based delivery orchestration in v0.2.x.

## Auto-Continue Safety

`auto-continue` uses the central `FeatureDeliveryWorkflow` orchestrator to decide whether the next workflow step is safe to run automatically.

It will stop before actions that:

- require approval
- may generate patches
- may call an LLM
- write to external systems in risky ways

Example:

```bash
deliveryops auto-continue --repo . --max-steps 5
```

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

## License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for details.
