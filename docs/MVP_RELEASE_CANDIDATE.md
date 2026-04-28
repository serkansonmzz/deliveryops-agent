# DeliveryOps Agent MVP Release Candidate

## Status

DeliveryOps Agent is currently at MVP release candidate stage.

The system is CLI-first and designed for existing local Git repositories connected to GitHub.

## Core MVP Capabilities

- Initialize a local DeliveryOps workspace
- Track workflow state in `.deliveryops/state.json`
- Track human-readable progress in `.deliveryops/DELIVERY.md`
- Create GitHub issues
- Create feature branches
- Run lightweight architecture review
- Generate implementation plans
- Generate deterministic and Agno-powered patches
- Sanitize and validate generated patches
- Require approval before applying patches
- Detect and run safe test commands
- Analyze test failures
- Run release readiness checks
- Generate conventional commit messages
- Require approval before commit
- Commit approved changes
- Require approval before push
- Push feature branches
- Require approval before draft PR creation
- Open draft pull requests
- Comment progress on GitHub issues
- Generate final delivery reports
- Continue/resume workflows from state
- Auto-continue safe local steps
- Apply policy profiles
- Track agent role capabilities
- Check GitHub CI status
- Generate controlled fix patches after failures

## MVP Safety Rules

DeliveryOps is autonomous only where safe.

Approval is required for:

- Applying patches
- Creating commits
- Pushing branches
- Opening draft pull requests
- Other state-changing or external write actions

Blocked actions include:

- Force pushing
- Deleting repositories
- Deleting branches
- Direct push to main/master
- Modifying secrets
- Production deploys
- Arbitrary destructive shell commands

## Recommended MVP Demo Flow

```bash
deliveryops init --repo .

deliveryops run \
  --repo . \
  --github-owner my-user \
  --github-repo my-repo \
  --request "Update README documentation with a small DeliveryOps usage note."

deliveryops continue --repo .
deliveryops approval-status --repo .
deliveryops approve --repo . --action apply_patch --reason "Patch looks safe."
deliveryops apply-patch --repo .

deliveryops detect-tests --repo .
deliveryops run-tests --repo .
deliveryops readiness-check --repo .

deliveryops generate-commit-message --repo .
deliveryops approval-status --repo .
deliveryops approve --repo . --action git_commit --reason "Commit looks safe."
deliveryops commit --repo .

deliveryops approve --repo . --action git_push --reason "Push approved."
deliveryops push --repo .

deliveryops approve --repo . --action create_draft_pull_request --reason "Draft PR approved."
deliveryops open-draft-pr --repo .

deliveryops comment-progress --repo .
deliveryops final-report --repo .
```

## MVP Release Checklist

- [ ] All tests pass
- [ ] `deliveryops smoke-test --repo .` passes
- [ ] README is up to date
- [ ] Known limitations are documented
- [ ] Workflow overview is documented
- [ ] CLI help text is usable
- [ ] `.deliveryops/` runtime files are ignored
- [ ] No secrets are committed
- [ ] Release readiness check runs
