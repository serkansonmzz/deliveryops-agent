# Known Limitations

DeliveryOps Agent is currently an MVP release candidate.

## Current Limitations

- The workflow is CLI-first only.
- There is no web UI.
- Jira and Trello are not supported.
- Draft PR creation depends on GitHub CLI authentication.
- CI status detection depends on `gh pr checks`.
- Patch generation may still require human review.
- Agno Dev Agent patch generation depends on an OpenAI API key.
- Multi-file code generation is intentionally conservative.
- No automatic merge is supported.
- No production deployment is supported.
- No secret modification is allowed.
- No destructive shell command execution is allowed.
- Resume logic is state-based and assumes `.deliveryops/state.json` is intact.
- Policy profiles are deterministic and intentionally simple.
- Release readiness is heuristic, not a substitute for human review.

## Recommended Usage

Use DeliveryOps for:

- personal repositories
- sandbox projects
- controlled MVP feature workflows
- assisted delivery tracking
- patch proposal and review workflows

Avoid using DeliveryOps unattended on:

- production repositories
- security-sensitive repositories
- repositories with complex release processes
- repositories where CI/CD has irreversible side effects
