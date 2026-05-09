from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.schemas.dev_patch_context import DevContextFile, DevPatchContext


MAX_FILE_BYTES = 12_000

BLOCKED_FILE_PATTERNS = [
    ".env",
    ".env.local",
    ".env.production",
    "secrets",
    "credentials",
    "id_rsa",
    "id_ed25519",
]

BINARY_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".sqlite",
    ".db",
}


def is_blocked_file(path: str) -> bool:
    lower = path.lower()
    return any(pattern in lower for pattern in BLOCKED_FILE_PATTERNS)


def is_binary_like(path: str) -> bool:
    return Path(path).suffix.lower() in BINARY_SUFFIXES


def safe_read_context_file(repo_path: Path, relative_path: str) -> str | None:
    if is_blocked_file(relative_path) or is_binary_like(relative_path):
        return None

    repo_root = repo_path.resolve()
    full_path = (repo_path / relative_path).resolve()
    try:
        full_path.relative_to(repo_root)
    except ValueError:
        return None

    if not full_path.exists() or not full_path.is_file():
        return None

    content = full_path.read_text(encoding="utf-8", errors="replace")
    if full_path.stat().st_size > MAX_FILE_BYTES:
        return content[:MAX_FILE_BYTES] + (
            "\n\n[TRUNCATED: file exceeded context limit]\n"
        )

    return content


def infer_file_kind(path: str) -> str:
    lower = path.lower()
    name = Path(path).name
    suffix = Path(path).suffix.lower()

    if lower.startswith("tests/") or name.startswith("test_") or "test" in name:
        return "test"
    if suffix in {".md", ".rst", ".txt"}:
        return "documentation"
    if suffix in {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".cs"}:
        return "source"
    if name in {"pyproject.toml", "package.json", "Dockerfile"} or lower.startswith(
        ".github/"
    ):
        return "config"
    return "unknown"


def deduplicate_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)

    return result


def collect_related_tests(state: DeliveryState, target_files: list[str]) -> list[str]:
    related: list[str] = []
    for target_file in target_files:
        related.extend(state.repo_source_test_map.get(target_file, []))
    return deduplicate_keep_order(related)


def select_dev_context_files(state: DeliveryState) -> list[str]:
    candidates: list[str] = []
    candidates.extend(state.implementation_plan_target_files)
    candidates.extend(state.likely_files)
    candidates.extend(state.patch_affected_files)
    candidates.extend(collect_related_tests(state, candidates))

    request = state.original_request.lower()
    if "readme" in request and "README.md" not in candidates:
        candidates.append("README.md")
    if "documentation" in request or "docs" in request:
        for file_path in state.likely_files:
            if file_path.endswith(".md") and file_path not in candidates:
                candidates.append(file_path)

    return deduplicate_keep_order(candidates)[:20]


def build_dev_patch_context(repo_path: Path, state: DeliveryState) -> DevPatchContext:
    selected_paths = select_dev_context_files(state)
    related_tests = collect_related_tests(state, selected_paths)
    context_files: list[DevContextFile] = []
    planned_new_files: list[str] = []

    for path in selected_paths:
        content = safe_read_context_file(repo_path, path)
        if content is None:
            full_path = (repo_path / path).resolve()
            try:
                full_path.relative_to(repo_path.resolve())
            except ValueError:
                continue

            if (
                not is_blocked_file(path)
                and not is_binary_like(path)
                and path in state.implementation_plan_target_files + state.likely_files
                and not full_path.exists()
            ):
                planned_new_files.append(path)
            continue

        reason = "Selected from implementation plan, likely files, or related tests."
        if path in state.implementation_plan_target_files:
            reason = "Selected because it is listed as an implementation target file."
        elif path in related_tests:
            reason = "Selected because it is related to a target source file."
        elif path in state.likely_files:
            reason = "Selected because repository analysis marked it as likely relevant."

        context_files.append(
            DevContextFile(
                path=path,
                content=content,
                reason=reason,
                kind=infer_file_kind(path),
            )
        )

    allowed_target_files = deduplicate_keep_order(
        state.implementation_plan_target_files
        or state.likely_files
        or [file.path for file in context_files]
    )

    return DevPatchContext(
        request=state.original_request,
        issue_url=state.github_issue_url,
        branch_name=state.branch_name,
        feature_title=state.feature_request_title,
        issue_title=state.issue_spec_title,
        architecture_summary=state.architecture_review_summary,
        architecture_recommended_approach=state.architecture_recommended_approach,
        architecture_risks=state.risk_notes,
        architecture_security_notes=state.security_notes,
        architecture_testing_notes=state.testing_notes,
        architecture_devops_notes=state.devops_notes,
        implementation_plan_summary=state.implementation_plan_summary,
        implementation_plan_steps=state.implementation_plan_steps,
        implementation_target_files=state.implementation_plan_target_files,
        implementation_test_strategy=state.implementation_plan_test_strategy,
        implementation_risks=state.implementation_plan_risks,
        selected_files=context_files,
        related_tests=related_tests,
        risky_files=state.repo_risky_files,
        planned_new_files=deduplicate_keep_order(planned_new_files),
        allowed_target_files=allowed_target_files,
        blocked_file_patterns=BLOCKED_FILE_PATTERNS,
        patch_rules=[
            "Prefer structured file_edits over raw unified_diff.",
            "Use file_edits with create_file, replace_text, append_after, or append_to_file when possible.",
            "Use exact anchors from selected file content for replace_text and append_after.",
            "Use unified_diff only as a fallback for changes that cannot be expressed as file_edits.",
            "Do not include markdown fences around the diff.",
            "Keep the patch minimal and focused.",
            "Only modify files that are relevant to the implementation plan.",
            "Do not modify secrets, credentials, or environment files.",
            "Do not perform broad refactors.",
            "Prefer updating existing files.",
            "Include tests only when the implementation plan or change type requires them.",
        ],
        policy_profile=getattr(state, "policy_profile", None),
    )


def apply_dev_context_tracking_to_state(
    state: DeliveryState,
    context: DevPatchContext,
) -> None:
    state.dev_context_selected_files = [file.path for file in context.selected_files]
    state.dev_context_related_tests = context.related_tests
    state.dev_context_risky_files = context.risky_files
    state.dev_context_planned_new_files = context.planned_new_files
    state.dev_context_status = "prepared"
