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