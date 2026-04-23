import pytest

from app.tools.patch_validator_tools import (
    validate_unified_diff,
    validate_unified_diff_or_raise,
)


def test_validate_unified_diff_accepts_valid_patch():
    patch = """diff --git a/README.md b/README.md
index 1111111..2222222 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Test
+New line
"""

    errors = validate_unified_diff(patch)

    assert errors == []


def test_validate_unified_diff_rejects_missing_patch_header():
    patch = """@@ -1 +1,2 @@
 # Test
+New line
"""

    errors = validate_unified_diff(patch)

    assert "Patch must start with 'diff --git ' or '--- a/'." in errors


def test_validate_unified_diff_or_raise_rejects_invalid_patch():
    patch = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
"""

    with pytest.raises(RuntimeError):
        validate_unified_diff_or_raise(patch)

def test_validate_unified_diff_accepts_plain_unified_diff():
    patch = """--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Test
+New line
"""

    errors = validate_unified_diff(patch)

    assert errors == []