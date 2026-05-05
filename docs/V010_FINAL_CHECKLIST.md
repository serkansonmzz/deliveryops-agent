# v0.1.0 Final Release Checklist

Use this checklist before creating the final `v0.1.0` release.

## Code Quality

- [ ] `uv run pytest -q` passes
- [ ] `uv run deliveryops smoke-test --repo .` passes
- [ ] No unexpected files appear in `git status`
- [ ] `.deliveryops/` runtime files are ignored
- [ ] No secrets or local environment files are committed

## Documentation

- [ ] README explains what DeliveryOps Agent does
- [ ] README includes setup instructions
- [ ] README includes core commands
- [ ] README links to release candidate docs
- [ ] `docs/WORKFLOW_OVERVIEW.md` is accurate
- [ ] `docs/KNOWN_LIMITATIONS.md` is accurate
- [ ] `docs/DEMO_SCRIPT.md` is usable
- [ ] `docs/MANUAL_E2E_TEST.md` is usable

## CLI

- [ ] `uv run deliveryops --help` is readable
- [ ] Important commands have clear help text
- [ ] Risky commands require approval
- [ ] `continue` recommends the right next action
- [ ] `auto-continue` stops before risky actions

## GitHub Workflow

- [ ] GitHub issue creation works
- [ ] Feature branch creation works
- [ ] Draft PR creation works after approval
- [ ] Issue progress comment works
- [ ] CI watcher handles passed / failed / pending / no checks

## Safety

- [ ] `apply_patch` requires approval
- [ ] `git_commit` requires approval
- [ ] `git_push` requires approval
- [ ] `create_draft_pull_request` requires approval
- [ ] Protected branch guards work
- [ ] Policy profiles behave as expected

## Release

- [ ] `docs/MVP_RELEASE_NOTES.md` is current
- [ ] `v0.1.0-rc1` notes reviewed
- [ ] Final tag `v0.1.0` is created from `main`
- [ ] GitHub Release `v0.1.0` is created
