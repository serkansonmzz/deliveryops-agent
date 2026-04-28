# DeliveryOps Agent

Agno-powered autonomous software delivery manager.

## Goal

DeliveryOps Agent turns a feature request into a GitHub-based delivery workflow:

Feature request → GitHub Issue → Branch → Architecture review → Implementation plan → Patch → Tests → Commit approval → Push approval → Draft PR.

## MVP Status

Current phase:

- Local CLI
- Local state storage
- Human-readable `.deliveryops/DELIVERY.md`
- Basic Git inspection tools
- Tool permission policy

## Setup

```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync


## Usage

```bash
# Initialize a new workspace
deliveryops init --repo .

# Inspect repository
deliveryops inspect --repo .
    
# Run a new feature delivery workflow
deliveryops run --repo . --request "Add a healthcheck endpoint"

# Check status
deliveryops status --repo .

# Create an issue and run the flow
deliveryops run \
  --repo . \
  --github-owner my-user \
  --github-repo my-repo \
  --request "Add a healthcheck endpoint"

```

## Test Detection and Safe Test Runner

Detect a safe test command:

```bash
deliveryops detect-tests --repo .
```

Run the detected safe test command:

```bash
deliveryops run-tests --repo .
```

DeliveryOps only runs allowlisted test commands such as `uv run pytest -q`, `python -m pytest -q`, `pytest -q`, or package manager test commands.
```

## Release Readiness Check

Run a deterministic release readiness check before commit, push, or PR steps:

```bash
deliveryops readiness-check --repo .
```

The check reviews patch status, test status, approvals, changed files, commit state, risk notes, and pending blockers.

## Policy Profiles

DeliveryOps supports policy profiles for different risk environments:

```bash
deliveryops set-policy-profile --repo . --profile personal_repo
deliveryops policy-status --repo .
deliveryops policy-status --repo . --action git_push
```

Available profiles:

- `sandbox`: local experimentation and smoke testing
- `personal_repo`: default MVP behavior for personal repositories
- `production_repo`: stricter readiness and testing requirements before push or draft PR actions

## Approval Request Details

Inspect the current pending approval request:

```bash
deliveryops approval-status --repo .
```

Approval requests include:

- action name
- risk level
- affected files
- exact command
- expected result
- rollback note
- active policy profile

## Agent Roles

List the formal DeliveryOps agent roles:

```bash
deliveryops agent-roles --repo .
```

Inspect one role and update the DeliveryOps tracking file:

```bash
deliveryops agent-role-status --repo . --role dev_agent
```

DeliveryOps currently formalizes these roles:

- Intake Agent
- Product Owner Agent
- Architecture Council Agent
- Delivery Manager Agent
- GitHub Operator Agent
- Dev Agent
- Test Agent
- Release Judge Agent

## CI Watcher

Check GitHub PR checks / GitHub Actions status:

```bash
deliveryops check-ci --repo .
```

This command reads GitHub PR check status with GitHub CLI and updates `.deliveryops/state.json` plus `.deliveryops/DELIVERY.md`.

## Smoke Test

Run a local end-to-end smoke test without touching the real GitHub repository:

```bash
deliveryops smoke-test --repo .

```
## Continue Workflow
Resume a partially completed DeliveryOps workflow by asking for the next recommended command:

```bash
deliveryops continue --repo .

```
## Safe Auto-Continue

# Auto-continue until next human approval (safe actions only)
```bash
deliveryops auto-continue --repo .

```
## Test Failure Analysis

Analyze a failed test run and get likely causes plus recommended next actions:

```bash
deliveryops analyze-test-failure --repo .
```