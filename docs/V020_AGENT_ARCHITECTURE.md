# DeliveryOps Agent v0.2.0 Agent Architecture

## Goal

v0.2.0 deepens DeliveryOps from a CLI-first delivery workflow into a clearer agent-team architecture.

The v0.1.0 release candidate already includes:

- GitHub issue workflow
- feature branches
- architecture review tracking
- patch generation and validation
- approval gates
- tests
- readiness checks
- commit / push / draft PR workflow
- CI watcher
- controlled fix patch loop
- final reports

v0.2.0 focuses on formalizing the agent layer.

## Agent Roles

DeliveryOps defines these core agents:

- Intake Agent
- Product Owner Agent
- Architecture Council Agent
- Delivery Manager Agent
- GitHub Operator Agent
- Dev Agent
- Test Agent
- Release Judge Agent

## Architecture Direction

The agent layer should move toward:

```text
prompts/*.md
→ AgentDefinition
→ Agno Agent factory
→ structured outputs
→ feature_delivery_workflow
→ tools
→ state.json + DELIVERY.md
```

## v0.2.0 Phase 32 Scope

Phase 32 introduces:

- prompt files
- prompt loader
- agent definitions
- Agno agent factory
- initial structured output mapping
- tests for prompt loading and agent definitions

## Non-goals for Phase 32

- Do not rewrite the full workflow.
- Do not remove existing CLI commands.
- Do not force all tools through Agno yet.
- Do not introduce MCP yet.
- Do not add Jira/Trello.

## Phase 37: Intake + Product Owner Integration

Phase 37 connects the first two formal agents to the delivery workflow:

```text
raw request
→ Intake Agent
→ FeatureRequest
→ Product Owner Agent
→ IssueSpec
→ GitHub issue
```

Both agents use structured output contracts and deterministic fallbacks.

## Phase 38: Better Repository Analysis

Phase 38 improves evidence collection before agent reasoning.

It adds:

- repository file scanning
- stack detection
- source/test file classification
- risky file detection
- likely file scoring
- source-to-test mapping

This gives Architecture Council, Dev Agent, Test Agent, and Release Judge better context.
