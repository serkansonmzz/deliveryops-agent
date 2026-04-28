# DeliveryOps Agent MVP Release Notes

## Status

release_candidate

## Summary

DeliveryOps Agent MVP provides a CLI-first, approval-gated, GitHub-based software delivery workflow for existing repositories.

## Core Capabilities

- GitHub issue creation
- Feature branch workflow
- Architecture review and implementation planning
- Patch generation and validation
- Approval-gated patch application
- Safe test detection and execution
- Test failure analysis
- Release readiness checks
- Approval-gated commit, push, and draft PR creation
- GitHub issue progress comments
- Final delivery reports
- Workflow continue and safe auto-continue
- Policy profiles
- Agent role registry
- CI watcher
- Controlled fix patch loop

## Release Checklist

- [ ] All unit tests pass.
- [ ] End-to-end smoke test passes.
- [ ] README is up to date.
- [ ] Workflow overview is documented.
- [ ] Known limitations are documented.
- [ ] Runtime files are excluded from Git.
- [ ] No secrets are committed.
- [ ] Release readiness check is available.

## Known Limitations

See `docs/KNOWN_LIMITATIONS.md`.
