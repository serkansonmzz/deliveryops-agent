# DeliveryOps Agent Demo Script

This demo shows how DeliveryOps Agent turns a feature request into an approval-gated GitHub delivery workflow.

## Prerequisites

- Python 3.12+
- `uv`
- Git
- GitHub CLI authenticated with `gh auth login`
- Existing GitHub repository
- Clean local working tree

## Demo Goal

Use DeliveryOps to run a small documentation change through the delivery workflow.

Example request:

```text
Update README documentation with a short section explaining DeliveryOps Agent's approval-gated workflow.
```

## Step 1: Prepare the repository

```bash
git switch main
git pull origin main
git status
```

Expected:

```text
nothing to commit, working tree clean
```

## Step 2: Run tests before demo

```bash
uv run pytest -q
```

Expected:

```text
all tests passed
```

## Step 3: Start a delivery workflow

```bash
uv run deliveryops run \
  --repo . \
  --github-owner YOUR_GITHUB_USER \
  --github-repo YOUR_REPO \
  --request "Update README documentation with a short section explaining DeliveryOps Agent's approval-gated workflow."
```

Expected:

- GitHub issue is created
- Feature branch is created
- `.deliveryops/state.json` is updated
- `.deliveryops/DELIVERY.md` is updated
- Workflow waits for `apply_patch` approval

## Step 4: Inspect current workflow state

```bash
uv run deliveryops continue --repo .
uv run deliveryops approval-status --repo .
cat .deliveryops/DELIVERY.md
```

## Step 5: Approve and apply patch

```bash
uv run deliveryops approve \
  --repo . \
  --action apply_patch \
  --reason "Patch looks safe for the demo."

uv run deliveryops apply-patch --repo .
```

## Step 6: Run tests and readiness check

```bash
uv run deliveryops detect-tests --repo .
uv run deliveryops run-tests --repo .
uv run deliveryops readiness-check --repo .
```

## Step 7: Generate and approve commit

```bash
uv run deliveryops generate-commit-message --repo .
uv run deliveryops approval-status --repo .

uv run deliveryops approve \
  --repo . \
  --action git_commit \
  --reason "Commit message and changed files look correct."

uv run deliveryops commit --repo .
```

## Step 8: Push branch

```bash
uv run deliveryops approve \
  --repo . \
  --action git_push \
  --reason "Push approved for demo branch."

uv run deliveryops push --repo .
```

## Step 9: Open draft PR

```bash
uv run deliveryops approve \
  --repo . \
  --action create_draft_pull_request \
  --reason "Draft PR approved for review."

uv run deliveryops open-draft-pr --repo .
```

## Step 10: Check CI and produce final report

```bash
uv run deliveryops check-ci --repo .
uv run deliveryops comment-progress --repo .
uv run deliveryops final-report --repo .
```

## Step 11: Review outputs

```bash
cat .deliveryops/DELIVERY.md
cat .deliveryops/FINAL_REPORT.md
```

## Demo Success Criteria

- GitHub issue exists
- Feature branch exists
- Draft PR exists
- Tests pass or failure is clearly reported
- DELIVERY.md is updated
- FINAL_REPORT.md is generated
- Risky actions required approval
