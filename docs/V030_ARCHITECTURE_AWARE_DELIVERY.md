# DeliveryOps Agent v0.3 Architecture-aware Delivery

v0.3 focuses on making DeliveryOps more architecture-aware before patch generation.

The first capability is Architecture Council Agent Integration.

## Phase 43: Architecture Council Agent Integration

Phase 43 connects the Architecture Council Agent to the delivery workflow.

The flow is:

```text
FeatureRequest
+ IssueSpec
+ RepoAnalysis
+ PolicyProfile
→ Architecture Council Agent
→ ArchitectureReview
→ state.json + DELIVERY.md
```

The Architecture Council Agent produces:

- affected areas
- recommended approach
- architecture risks
- security notes
- testing notes
- DevOps notes
- open questions
- confidence score

The agent is structured-output based and has a deterministic fallback.

## Safety Boundary

The Architecture Council Agent only produces review context.

It does not:

- apply patches
- create commits
- push branches
- create pull requests
- bypass approval gates
- make final policy or release decisions

The goal is to improve planning, patch context, risk awareness, and test guidance before implementation.

## Phase 44: Implementation Plan Agent / Planner Upgrade

Phase 44 upgrades implementation planning.

The flow is:

```text
FeatureRequest
+ IssueSpec
+ RepoAnalysis
+ ArchitectureReview
→ Implementation Planner Agent
→ ImplementationPlan
```

The plan includes:

- actionable steps
- target files
- expected changes
- test impact
- risk level
- acceptance mapping
- rollback notes
- confidence score

The planner uses structured output and has a deterministic fallback.

## Planner Safety Boundary

The Implementation Planner Agent only produces planning context.

It does not:

- write code
- generate patches
- apply patches
- create commits
- push branches
- create pull requests
- bypass approval gates

This keeps the workflow separation explicit:

```text
Planner plans.
Dev Agent proposes patches.
Apply Patch tool applies approved changes.
```

## Phase 45: Dev Agent Context Contract Upgrade

Phase 45 introduces a structured `DevPatchContext` before Dev Agent patch generation.

The flow is:

```text
FeatureRequest
+ IssueSpec
+ RepoAnalysis
+ ArchitectureReview
+ ImplementationPlan
+ selected file contents
+ related tests
+ policy constraints
+ patch rules
→ DevPatchContext
→ Dev Agent
→ AgentPatchResponse
```

The context contract includes:

- selected repository files with reasons
- related test files
- architecture and implementation planning notes
- risky files
- allowed target files
- blocked secret/environment patterns
- explicit patch rules

The Dev Agent still only proposes a patch. It does not apply patches, commit, push, create pull requests, or bypass approval gates.

## Phase 48: Deterministic Patch Builder & LLM Runtime Polish

Phase 48 reduces the workflow's dependency on LLM-generated unified diff formatting.

The preferred flow is:

```text
DevPatchContext
→ Dev Agent
→ structured file_edits
→ deterministic patch builder
→ strict patch validation
→ approval gate
```

The Dev Agent can still return `unified_diff` as a compatibility fallback, but structured edit intents are preferred for normal file edits.

Phase 48 also adds:

- per-agent model routing with environment overrides
- controlled LLM call timeouts
- agent timing logs in `.deliveryops/logs/agent_timing.json`
- visible attempt progress for Dev Agent patch generation
- elapsed heartbeat output for long-running commands
- final report notes for patch generation attempts and validation failures
- fast planning mode through `deliveryops run --fast` and `--no-llm-planning`

The safety boundary remains unchanged: Dev Agent proposes changes only, and patch application still requires explicit approval.
