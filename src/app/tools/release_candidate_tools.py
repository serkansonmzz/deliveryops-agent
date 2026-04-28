from pathlib import Path

from app.schemas.delivery_state import DeliveryState


RELEASE_CHECKLIST_ITEMS = [
    "All unit tests pass.",
    "End-to-end smoke test passes.",
    "README is up to date.",
    "Workflow overview is documented.",
    "Known limitations are documented.",
    "Runtime files are excluded from Git.",
    "No secrets are committed.",
    "Release readiness check is available.",
]


def build_mvp_release_notes(state: DeliveryState) -> str:
    lines: list[str] = []

    lines.append("# DeliveryOps Agent MVP Release Notes")
    lines.append("")
    lines.append("## Status")
    lines.append("")
    lines.append(state.mvp_release_status or "release_candidate")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(
        "DeliveryOps Agent MVP provides a CLI-first, approval-gated, "
        "GitHub-based software delivery workflow for existing repositories."
    )
    lines.append("")

    lines.append("## Core Capabilities")
    lines.append("")
    for item in [
        "GitHub issue creation",
        "Feature branch workflow",
        "Architecture review and implementation planning",
        "Patch generation and validation",
        "Approval-gated patch application",
        "Safe test detection and execution",
        "Test failure analysis",
        "Release readiness checks",
        "Approval-gated commit, push, and draft PR creation",
        "GitHub issue progress comments",
        "Final delivery reports",
        "Workflow continue and safe auto-continue",
        "Policy profiles",
        "Agent role registry",
        "CI watcher",
        "Controlled fix patch loop",
    ]:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("## Release Checklist")
    lines.append("")
    for item in state.mvp_release_checklist or RELEASE_CHECKLIST_ITEMS:
        lines.append(f"- [ ] {item}")

    lines.append("")
    lines.append("## Known Limitations")
    lines.append("")
    lines.append("See `docs/KNOWN_LIMITATIONS.md`.")
    lines.append("")

    return "\n".join(lines)


def write_mvp_release_notes(repo_path: Path, state: DeliveryState) -> Path:
    docs_dir = repo_path / "docs"
    docs_dir.mkdir(exist_ok=True)

    output_path = docs_dir / "MVP_RELEASE_NOTES.md"
    output_path.write_text(build_mvp_release_notes(state), encoding="utf-8")

    return output_path


def apply_mvp_release_candidate_state(state: DeliveryState, notes_path: Path, repo_path: Path) -> None:
    state.mvp_release_status = "release_candidate"
    state.mvp_release_notes_path = str(notes_path.relative_to(repo_path))
    state.mvp_release_checklist = RELEASE_CHECKLIST_ITEMS
    state.mark_completed("mvp_release_candidate_hardening")
