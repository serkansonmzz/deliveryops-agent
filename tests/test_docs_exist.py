from pathlib import Path


def test_release_docs_exist():
    required_docs = [
        "docs/MVP_RELEASE_CANDIDATE.md",
        "docs/WORKFLOW_OVERVIEW.md",
        "docs/KNOWN_LIMITATIONS.md",
        "docs/MVP_RELEASE_NOTES.md",
        "docs/DEMO_SCRIPT.md",
        "docs/MANUAL_E2E_TEST.md",
        "docs/V010_FINAL_CHECKLIST.md",
    ]

    for doc_path in required_docs:
        path = Path(doc_path)
        assert path.exists(), f"Missing required doc: {doc_path}"
        assert path.read_text(encoding="utf-8").strip(), f"Empty doc: {doc_path}"
