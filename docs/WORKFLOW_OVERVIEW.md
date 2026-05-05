# DeliveryOps Workflow Overview

DeliveryOps Agent turns a feature request into a GitHub-based delivery workflow.

## High-Level Flow

```text
Feature request
→ repository inspection
→ local workspace initialization
→ GitHub issue
→ feature branch
→ architecture review
→ implementation plan
→ patch generation
→ approval
→ patch application
→ test detection
→ test execution
→ readiness check
→ commit message generation
→ commit approval
→ git commit
→ push approval
→ git push
→ draft PR approval
→ draft PR
→ CI check
→ issue progress comment
→ final report
```

## Human Tracking

DeliveryOps writes human-readable workflow state to:

```text
.deliveryops/DELIVERY.md
```

## Machine State

DeliveryOps writes resumable workflow state to:

```text
.deliveryops/state.json
```

## Approval History

DeliveryOps records approvals in:

```text
.deliveryops/approvals.md
```

## Continue Mode

Use:

```bash
deliveryops continue --repo .
```

to see the next recommended workflow step.

Use:

```bash
deliveryops auto-continue --repo .
```

to automatically execute safe local steps.

## Release Validation References

Use these supporting documents while preparing the final `v0.1.0` release:

- `docs/DEMO_SCRIPT.md`
- `docs/MANUAL_E2E_TEST.md`
- `docs/V010_FINAL_CHECKLIST.md`
