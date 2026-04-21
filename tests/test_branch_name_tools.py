from app.tools.branch_name_tools import (
    slugify_branch_text,
    build_feature_branch_name,
)


def test_slugify_branch_text():
    slug = slugify_branch_text("Add Branch Creation to DeliveryOps Run!")

    assert slug == "add-branch-creation-to-deliveryops-run"


def test_slugify_branch_text_empty():
    slug = slugify_branch_text("   ")

    assert slug == "feature-request"


def test_slugify_branch_text_truncates():
    slug = slugify_branch_text("x" * 120)

    assert len(slug) <= 48


def test_build_feature_branch_name_with_issue_number():
    branch = build_feature_branch_name(
        issue_number=7,
        request="Add Branch Creation to DeliveryOps Run",
    )

    assert branch == "feature/7-add-branch-creation-to-deliveryops-run"


def test_build_feature_branch_name_without_issue_number():
    branch = build_feature_branch_name(
        issue_number=None,
        request="Add Branch Creation",
    )

    assert branch == "feature/add-branch-creation"