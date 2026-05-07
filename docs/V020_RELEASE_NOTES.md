# DeliveryOps Agent v0.2.0 Release Notes

## Summary

DeliveryOps Agent v0.2.0 deepens the project from a working CLI-first MVP into a more structured agentic delivery architecture.

The release focuses on:

- modular CLI organization
- application service boundaries
- lightweight ports/adapters
- formal agent architecture foundation
- Intake and Product Owner agent integration
- better repository analysis
- hardened GitHub / CI integration
- central FeatureDeliveryWorkflow orchestration
- safer auto-continue behavior

## Highlights

### Agent Architecture Foundation

v0.2.0 introduces formal agent definitions and prompt files for the core DeliveryOps roles:

- Intake Agent
- Product Owner Agent
- Architecture Council Agent
- Delivery Manager Agent
- GitHub Operator Agent
- Dev Agent
- Test Agent
- Release Judge Agent

Not every role is a full LLM-backed agent. Some roles intentionally remain deterministic tool/service boundaries.

### Intake + Product Owner Agent Integration

Raw feature requests can now move through a structured flow:

```text
raw request
→ FeatureRequest
→ IssueSpec
→ GitHub issue
```

If an LLM is unavailable or returns unusable output, DeliveryOps falls back to deterministic issue generation.

### Repository Analysis

DeliveryOps can analyze repository structure and enrich workflow state with:

- detected stack
- source files
- test files
- documentation files
- config files
- risky files
- likely files
- source-to-test mapping

### Workflow Orchestration

v0.2.0 introduces `FeatureDeliveryWorkflow` as the central workflow decision boundary.

It helps align:

- `continue`
- `auto-continue`
- safe action detection
- approval-required action detection
- manual-trigger guards for patch/LLM actions

### GitHub / CI Hardening

The CI watcher now handles more external-world edge cases:

- missing GitHub CLI
- missing authentication
- missing PR
- no checks
- pending checks
- failed checks
- JSON check parsing

### Safety

Risky operations remain approval-gated:

- apply patch
- commit
- push
- create draft PR

Auto-continue does not run patch generation, LLM-triggered patch generation, or approval-required operations.

## Validation

Before release, run:

```bash
uv run python -m compileall src
uv run pytest -q
uv run deliveryops smoke-test --repo .
```

## Known Limitations

DeliveryOps Agent v0.2.0 is still a CLI-first, local-repository workflow assistant.

It does not provide:

- automatic merge
- production deployment
- Jira/Trello integration
- MCP integration
- full autonomous coding without approval
- web UI
- complex multi-repository orchestration

See `docs/KNOWN_LIMITATIONS.md`.
