def strip_markdown_fences(text: str) -> str:
    lines: list[str] = []

    for line in text.replace("\r\n", "\n").split("\n"):
        if line.strip().startswith("```"):
            continue
        lines.append(line)

    return "\n".join(lines)


def sanitize_agent_patch_output(raw_text: str) -> str:
    cleaned = strip_markdown_fences(raw_text).replace("\r\n", "\n").strip()

    if not cleaned:
        return ""

    diff_git_index = cleaned.find("diff --git ")
    plain_diff_index = cleaned.find("--- a/")

    if diff_git_index != -1:
        patch_text = cleaned[diff_git_index:]
    elif plain_diff_index != -1:
        patch_text = cleaned[plain_diff_index:]
    else:
        return ""

    return patch_text.strip() + "\n"