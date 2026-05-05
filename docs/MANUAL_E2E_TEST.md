# Manual End-to-End Test

This document describes the manual validation flow for DeliveryOps Agent v0.1.0.

## Purpose

Verify that DeliveryOps Agent can run the core MVP workflow on a real local repository connected to GitHub.

## Test Environment

Record these before running the test:

```text
Date:
OS:
Python version:
uv version:
Git version:
GitHub CLI version:
Repository:
Branch:
DeliveryOps version/tag:
```

## Pre-checks

```bash
git switch main
git pull origin main
git status
uv run pytest -q
uv run deliveryops smoke-test --repo .
```

Expected:

- Working tree is clean before test
- Unit tests pass
- Smoke test passes

## Manual Workflow

### 1. Start workflow

```bash
uv run deliveryops run \
  --repo . \
  --github-owner YOUR_GITHUB_USER \
  --github-repo YOUR_REPO \
  --request "Update README documentation with a small DeliveryOps usage note."
```

Expected:

- GitHub issue is created
- Feature branch is created
- DeliveryOps workspace is initialized
- Approval is requested for patch application

### 2. Continue/status check

```bash
uv run deliveryops continue --repo .
uv run deliveryops approval-status --repo .
```

Expected:

- Next action is clear
- Approval details include risk level, affected files, expected result, and rollback note

### 3. Apply patch

```bash
uv run deliveryops approve --repo . --action apply_patch --reason "Manual E2E approval."
uv run deliveryops apply-patch --repo .
```

Expected:

- Patch applies cleanly
- Changed files are tracked
- DELIVERY.md is updated

### 4. Test and readiness

```bash
uv run deliveryops detect-tests --repo .
uv run deliveryops run-tests --repo .
uv run deliveryops readiness-check --repo .
```

Expected:

- Test command is detected
- Tests pass or failure analysis is available
- Readiness status is `ready` or clearly explains blockers/warnings

### 5. Commit

```bash
uv run deliveryops generate-commit-message --repo .
uv run deliveryops approval-status --repo .
uv run deliveryops approve --repo . --action git_commit --reason "Commit approved."
uv run deliveryops commit --repo .
```

Expected:

- Commit is created
- Commit hash is recorded in state and DELIVERY.md

### 6. Push

```bash
uv run deliveryops approve --repo . --action git_push --reason "Push approved."
uv run deliveryops push --repo .
```

Expected:

- Feature branch is pushed
- Push status is recorded

### 7. Draft PR

```bash
uv run deliveryops approve --repo . --action create_draft_pull_request --reason "Draft PR approved."
uv run deliveryops open-draft-pr --repo .
```

Expected:

- Draft PR is created
- PR URL is recorded

### 8. CI and final report

```bash
uv run deliveryops check-ci --repo .
uv run deliveryops comment-progress --repo .
uv run deliveryops final-report --repo .
```

Expected:

- CI status is recorded if available
- GitHub issue gets a progress comment
- FINAL_REPORT.md is generated

## Pass Criteria

- Unit tests pass
- Smoke test passes
- Manual E2E workflow completes or blocks with clear reason
- No unsafe operation runs without approval
- `.deliveryops/` runtime files are not committed
- GitHub issue, branch, and draft PR are created as expected
- FINAL_REPORT.md is useful and readable

## Cleanup

If needed:

```bash
git switch main
git pull origin main
git branch -D FEATURE_BRANCH_NAME
git push origin --delete FEATURE_BRANCH_NAME
```

Close demo PR and issue manually if they were only created for validation.
