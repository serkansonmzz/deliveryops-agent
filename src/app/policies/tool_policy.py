from enum import StrEnum


class ToolPermission(StrEnum):
    SAFE = "safe"
    APPROVAL_REQUIRED = "approval_required"
    BLOCKED = "blocked"


SAFE_TOOLS = {
    "read_repo_tree",
    "read_file",
    "inspect_git_status",
    "inspect_git_diff",
    "detect_project_stack",
    "detect_test_commands",
    "create_github_issue",
    "add_github_issue_comment",
    "create_branch",
    "generate_patch",
    "update_delivery_markdown",
    "update_state_json",
    "run_safe_tests",
}

APPROVAL_REQUIRED_TOOLS = {
    "apply_patch",
    "git_commit",
    "git_push",
    "create_draft_pull_request",
    "close_github_issue",
    "create_release_tag",
    "modify_env_files",
}

BLOCKED_TOOLS = {
    "force_push",
    "delete_repository",
    "delete_branch",
    "push_to_main_or_master_directly",
    "modify_secrets",
    "production_deploy",
    "arbitrary_shell_command",
    "destructive_file_operations",
}


def get_tool_permission(tool_name: str) -> ToolPermission:
    if tool_name in SAFE_TOOLS:
        return ToolPermission.SAFE

    if tool_name in APPROVAL_REQUIRED_TOOLS:
        return ToolPermission.APPROVAL_REQUIRED

    if tool_name in BLOCKED_TOOLS:
        return ToolPermission.BLOCKED

    return ToolPermission.BLOCKED


def assert_tool_allowed(tool_name: str) -> None:
    permission = get_tool_permission(tool_name)

    if permission == ToolPermission.BLOCKED:
        raise PermissionError(f"Tool is blocked by policy: {tool_name}")