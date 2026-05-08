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

## LLM-backed vs Deterministic Roles

DeliveryOps separates agent roles from LLM calls.

Some roles may use LLMs for reasoning or structured output:

- Intake Agent
- Product Owner Agent
- Architecture Council Agent
- Dev Agent
- Release Judge Agent

Some roles should remain mostly deterministic:

- GitHub Operator Agent
- Test Agent test runner behavior
- Delivery Manager workflow gate behavior
- Policy and approval enforcement

The guiding principle is:

```text
LLM agents reason and propose.
Deterministic tools execute and enforce.
Policy and approval gates decide risky actions.
```

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

## Phase 39: GitHub / CI Adapter Hardening

Phase 39 improves GitHub and CI integration reliability.

It adds:

- GitHub CLI availability checks
- authentication error handling
- missing PR handling
- JSON-based PR check parsing
- CI status normalization
- better CI error reporting in state and DELIVERY.md

## Phase 40: FeatureDeliveryWorkflow Orchestrator

Phase 40 introduces the central workflow orchestration boundary.

The first version wraps the existing deterministic workflow decision logic and exposes a stable `FeatureDeliveryWorkflow` class.

Responsibilities:

- determine the next workflow step
- identify safe-to-run actions
- identify approval-required actions
- describe the current workflow position
- provide a future integration point for Agno workflow orchestration

## Phase 41: Auto-Continue Orchestrator Integration

Phase 41 connects `auto-continue` to the central `FeatureDeliveryWorkflow` boundary.

The orchestrator now decides whether the next step is:

- safe to run automatically
- approval-required
- blocked
- manually triggered because it may call an LLM or generate patches

This keeps `continue` and `auto-continue` aligned around the same workflow decision model.

## v0.3 Forward Path

The next architecture line is `v0.3 = Architecture-aware DeliveryOps`.

Phase 43 starts that line by connecting the Architecture Council Agent to repository evidence and workflow state:

```text
FeatureRequest
+ IssueSpec
+ RepoAnalysis
→ Architecture Council Agent
→ ArchitectureReview
```

See `docs/V030_ARCHITECTURE_AWARE_DELIVERY.md`.
