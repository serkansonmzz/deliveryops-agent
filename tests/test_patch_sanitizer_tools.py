from app.tools.patch_sanitizer_tools import (
    strip_markdown_fences,
    sanitize_agent_patch_output,
)


def test_strip_markdown_fences():
    raw = """```diff
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Test
+New line
```"""

    cleaned = strip_markdown_fences(raw)

    assert "```" not in cleaned
    assert "diff --git a/README.md b/README.md" in cleaned


def test_sanitize_agent_patch_output_from_noisy_text():
    raw = """
Here is your patch:

```diff
diff --git a/README.md b/README.md
index 1111111..2222222 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Test
+New line
"""

