from app.schemas.patch_proposal import PatchProposal


def build_patch_proposal(
    request: str,
    likely_files: list[str],
    implementation_plan: list[str],
) -> PatchProposal:
    affected_files = likely_files[:10]

    proposed_changes: list[str] = []

    if implementation_plan:
        proposed_changes.extend(implementation_plan[:5])
    else:
        proposed_changes.append("Inspect the codebase and identify the minimal code change needed.")

    request_lower = request.lower()

    if "git" in request_lower or "branch" in request_lower:
        risk_level = "medium"
    elif "delete" in request_lower or "remove" in request_lower:
        risk_level = "high"
    else:
        risk_level = "low"

    if not affected_files:
        affected_files = ["To be determined during patch generation."]

    summary = (
        "A patch proposal was prepared from the architecture review and implementation plan. "
        "No files have been modified yet. Applying the patch requires explicit user approval."
    )

    return PatchProposal(
        summary=summary,
        affected_files=affected_files,
        proposed_changes=proposed_changes,
        risk_level=risk_level,
        requires_approval=True,
    )