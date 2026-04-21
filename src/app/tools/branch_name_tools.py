import re


def slugify_branch_text(text: str, max_length: int = 48) -> str:
    cleaned = text.strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned)
    cleaned = cleaned.strip("-")

    if not cleaned:
        return "feature-request"

    if len(cleaned) <= max_length:
        return cleaned

    return cleaned[:max_length].rstrip("-")


def build_feature_branch_name(issue_number: int | None, request: str) -> str:
    slug = slugify_branch_text(request)

    if issue_number is None:
        return f"feature/{slug}"

    return f"feature/{issue_number}-{slug}"