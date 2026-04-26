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
