from pathlib import Path

from app.schemas.repo_analysis import FileSignal, RepoAnalysisResult


IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".deliveryops",
    "node_modules",
    "dist",
    "build",
    ".mypy_cache",
    ".ruff_cache",
}

SOURCE_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".cs",
}

DOC_SUFFIXES = {
    ".md",
    ".rst",
    ".txt",
}

CONFIG_NAMES = {
    "pyproject.toml",
    "uv.lock",
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "Dockerfile",
    "docker-compose.yml",
    "compose.yml",
}

RISKY_NAME_PARTS = {
    ".env",
    "secret",
    "secrets",
    "token",
    "credential",
    "credentials",
    "deploy",
    "migration",
    "docker",
    "workflow",
}


def should_ignore(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def list_repo_files(repo_path: Path, max_files: int = 2000) -> list[str]:
    files: list[str] = []

    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue

        relative = path.relative_to(repo_path)

        if should_ignore(relative):
            continue

        files.append(str(relative))

        if len(files) >= max_files:
            break

    return sorted(files)


def detect_stack_from_files(files: list[str]) -> list[str]:
    detected: list[str] = []
    file_set = set(files)

    if "pyproject.toml" in file_set or any(file.endswith(".py") for file in files):
        detected.append("python")

    if "uv.lock" in file_set:
        detected.append("uv")

    if "package.json" in file_set:
        detected.append("node")

    if any(file.endswith((".ts", ".tsx")) for file in files):
        detected.append("typescript")

    if any(file.endswith((".js", ".jsx")) for file in files):
        detected.append("javascript")

    if any(file.endswith(".go") for file in files):
        detected.append("go")

    if any(file.endswith(".rs") for file in files):
        detected.append("rust")

    if any(file.startswith(".github/workflows/") for file in files):
        detected.append("github_actions")

    if "Dockerfile" in file_set or any("docker-compose" in file for file in files):
        detected.append("docker")

    if "README.md" in file_set:
        detected.append("readme")

    return detected


def detect_project_stack(repo_path: Path) -> list[str]:
    return detect_stack_from_files(list_repo_files(repo_path))


def classify_files(files: list[str]) -> tuple[list[str], list[str], list[str], list[str]]:
    source_files: list[str] = []
    test_files: list[str] = []
    documentation_files: list[str] = []
    config_files: list[str] = []

    for file_path in files:
        path = Path(file_path)
        lower = file_path.lower()
        is_test_file = (
            "/tests/" in f"/{lower}"
            or lower.startswith("tests/")
            or path.name.startswith("test_")
            or path.name.endswith("_test.py")
            or ".test." in path.name
            or ".spec." in path.name
        )

        if path.suffix in SOURCE_SUFFIXES and not is_test_file:
            source_files.append(file_path)

        if is_test_file:
            test_files.append(file_path)

        if path.suffix in DOC_SUFFIXES:
            documentation_files.append(file_path)

        if path.name in CONFIG_NAMES or lower.startswith(".github/workflows/"):
            config_files.append(file_path)

    return source_files, test_files, documentation_files, config_files


def detect_risky_files(files: list[str]) -> list[str]:
    risky: list[str] = []

    for file_path in files:
        lower = file_path.lower()

        if any(part in lower for part in RISKY_NAME_PARTS):
            risky.append(file_path)

    return risky


def normalize_token(text: str) -> str:
    return (
        text.lower()
        .replace("-", "_")
        .replace(" ", "_")
        .replace(".", "_")
        .strip("_")
    )


def classify_file_kind(file_path: str) -> str:
    path = Path(file_path)
    lower = file_path.lower()

    if lower.startswith("tests/") or "test" in path.name.lower():
        return "test"

    if path.suffix in DOC_SUFFIXES:
        return "documentation"

    if path.suffix in SOURCE_SUFFIXES:
        return "source"

    if path.name in CONFIG_NAMES or lower.startswith(".github/workflows/"):
        return "config"

    return "unknown"


def score_likely_file(file_path: str, request: str) -> FileSignal:
    lower_file = file_path.lower()
    lower_request = request.lower()
    score = 0
    reasons: list[str] = []
    path = Path(file_path)
    name_tokens = [
        token for token in normalize_token(path.stem).split("_") if len(token) >= 3
    ]

    for token in name_tokens:
        if token in lower_request:
            score += 5
            reasons.append(f"filename token `{token}` appears in request")

    if "readme" in lower_request and path.name.lower() == "readme.md":
        score += 20
        reasons.append("request mentions README")

    if "doc" in lower_request or "documentation" in lower_request:
        if path.suffix in DOC_SUFFIXES:
            score += 8
            reasons.append("request appears documentation-related")

    if "test" in lower_request and (
        lower_file.startswith("tests/") or "test" in path.name.lower()
    ):
        score += 8
        reasons.append("request mentions tests")

    if "github" in lower_request and lower_file.startswith(".github/"):
        score += 10
        reasons.append("request mentions GitHub")

    if "ci" in lower_request and lower_file.startswith(".github/workflows/"):
        score += 10
        reasons.append("request mentions CI")

    if "cli" in lower_request and "cli" in lower_file:
        score += 10
        reasons.append("request mentions CLI")

    if "agent" in lower_request and "agent" in lower_file:
        score += 6
        reasons.append("request mentions agent")

    if "policy" in lower_request and "policy" in lower_file:
        score += 6
        reasons.append("request mentions policy")

    if path.name in {"pyproject.toml", "package.json"}:
        if any(word in lower_request for word in ["dependency", "package", "install"]):
            score += 10
            reasons.append("request mentions dependency/package changes")

    return FileSignal(
        path=file_path,
        kind=classify_file_kind(file_path),
        score=score,
        reasons=reasons,
    )


def rank_likely_files(
    files: list[str],
    request: str,
    limit: int = 20,
) -> list[FileSignal]:
    scored = [score_likely_file(file_path, request) for file_path in files]
    relevant = [item for item in scored if item.score > 0]

    return sorted(
        relevant,
        key=lambda item: (-item.score, item.path),
    )[:limit]


def find_likely_files(repo_path: Path, request: str) -> list[str]:
    files = list_repo_files(repo_path)
    return [item.path for item in rank_likely_files(files, request)]


def guess_test_file_for_source(source_file: str, test_files: list[str]) -> list[str]:
    source_path = Path(source_file)
    candidates: list[str] = []
    stem = source_path.stem
    possible_names = {
        f"test_{stem}.py",
        f"{stem}_test.py",
        f"{stem}.test.ts",
        f"{stem}.spec.ts",
        f"{stem}.test.js",
        f"{stem}.spec.js",
    }

    for test_file in test_files:
        test_name = Path(test_file).name

        if test_name in possible_names:
            candidates.append(test_file)
            continue

        if stem.lower() in test_file.lower():
            candidates.append(test_file)

    return sorted(set(candidates))


def build_source_test_map(
    source_files: list[str],
    test_files: list[str],
) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}

    for source_file in source_files:
        matches = guess_test_file_for_source(source_file, test_files)

        if matches:
            mapping[source_file] = matches

    return mapping


def analyze_repository(repo_path: Path, request: str) -> RepoAnalysisResult:
    files = list_repo_files(repo_path)
    detected_stack = detect_stack_from_files(files)
    source_files, test_files, documentation_files, config_files = classify_files(files)
    risky_files = detect_risky_files(files)
    likely_files = rank_likely_files(files, request)
    source_test_map = build_source_test_map(source_files, test_files)
    summary = (
        f"Repository analysis found {len(files)} files, "
        f"{len(source_files)} source files, {len(test_files)} test files, "
        f"{len(documentation_files)} documentation files, and "
        f"{len(config_files)} config files. "
        f"Detected stack: {', '.join(detected_stack) if detected_stack else 'unknown'}."
    )

    return RepoAnalysisResult(
        detected_stack=detected_stack,
        source_files=source_files,
        test_files=test_files,
        documentation_files=documentation_files,
        config_files=config_files,
        risky_files=risky_files,
        likely_files=likely_files,
        source_test_map=source_test_map,
        summary=summary,
    )
