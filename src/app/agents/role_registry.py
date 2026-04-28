from app.schemas.agent_role import AgentRoleSpec


def get_agent_role_specs() -> dict[str, AgentRoleSpec]:
    roles = [
        AgentRoleSpec(
            role_id="intake_agent",
            display_name="Intake Agent",
            purpose="Convert a raw user feature request into a structured delivery request.",
            responsibilities=[
                "Extract user intent.",
                "Identify expected behavior.",
                "Identify constraints and assumptions.",
                "Avoid unnecessary clarification unless the request is impossible.",
            ],
            expected_outputs=[
                "Structured feature request",
                "Initial assumptions",
                "Initial risks",
            ],
            implemented_capabilities=[
                "Raw request is stored in DeliveryState.",
                "Request is propagated into GitHub issue body and delivery tracking.",
            ],
            future_capabilities=[
                "Dedicated structured FeatureRequest schema.",
                "Agno-based request normalization.",
                "Ambiguity scoring.",
            ],
        ),
        AgentRoleSpec(
            role_id="product_owner_agent",
            display_name="Product Owner Agent",
            purpose="Create a clear GitHub issue specification from a feature request.",
            responsibilities=[
                "Create issue title and body.",
                "Write acceptance criteria.",
                "Separate scope and out-of-scope.",
                "Make the work actionable.",
            ],
            expected_outputs=[
                "GitHub issue title",
                "GitHub issue body",
                "Acceptance criteria",
                "Definition of done",
            ],
            implemented_capabilities=[
                "GitHub issue creation exists.",
                "Issue body generation exists.",
                "Request-to-issue workflow exists.",
            ],
            future_capabilities=[
                "Dedicated Product Owner Agno agent.",
                "Structured issue quality scoring.",
                "Issue label strategy.",
            ],
        ),
        AgentRoleSpec(
            role_id="architecture_council_agent",
            display_name="Architecture Council Agent",
            purpose="Perform lightweight architecture review before implementation.",
            responsibilities=[
                "Identify affected areas.",
                "Identify risks.",
                "Identify security concerns.",
                "Identify testing and DevOps implications.",
                "Suggest implementation strategy.",
            ],
            expected_outputs=[
                "Architecture review summary",
                "Affected areas",
                "Risk notes",
                "Security notes",
                "Testing notes",
                "DevOps notes",
            ],
            implemented_capabilities=[
                "Architecture review fields exist in DeliveryState.",
                "Implementation plan generation exists.",
                "Risk, security, testing, and DevOps notes are tracked.",
                "Release readiness can consume risk/test evidence.",
            ],
            future_capabilities=[
                "Dedicated multi-agent Architecture Council.",
                "Confidence score.",
                "Critic/Judge architecture review loop.",
            ],
        ),
        AgentRoleSpec(
            role_id="delivery_manager_agent",
            display_name="Delivery Manager Agent",
            purpose="Coordinate the full delivery workflow and decide the next step.",
            responsibilities=[
                "Track workflow state.",
                "Respect approval gates.",
                "Update state.json and DELIVERY.md.",
                "Recommend or execute next safe actions.",
                "Produce final status.",
            ],
            expected_outputs=[
                "Current step",
                "Completed steps",
                "Pending approvals",
                "Next action",
                "Final status",
            ],
            implemented_capabilities=[
                "DeliveryState exists.",
                "DELIVERY.md tracking exists.",
                "continue command exists.",
                "safe auto-continue exists.",
                "final report generation exists.",
            ],
            future_capabilities=[
                "Full Agno workflow orchestration.",
                "Multi-run history.",
                "Automatic retry/resume policies.",
            ],
        ),
        AgentRoleSpec(
            role_id="github_operator_agent",
            display_name="GitHub Operator Agent",
            purpose="Perform GitHub operations through controlled tools.",
            responsibilities=[
                "Create GitHub issues.",
                "Post issue comments.",
                "Create draft pull requests after approval.",
                "Never merge pull requests in MVP.",
            ],
            expected_outputs=[
                "Issue URL",
                "Issue comment URL",
                "Draft PR URL",
            ],
            implemented_capabilities=[
                "GitHub issue creation exists.",
                "Issue progress comments exist.",
                "Draft PR creation exists.",
                "GitHub CLI integration exists.",
            ],
            future_capabilities=[
                "PR status inspection.",
                "GitHub Actions/CI watcher.",
                "Richer GitHub error recovery.",
            ],
        ),
        AgentRoleSpec(
            role_id="dev_agent",
            display_name="Dev Agent",
            purpose="Prepare implementation patches while respecting approval gates.",
            responsibilities=[
                "Inspect relevant files.",
                "Generate implementation plan.",
                "Generate code/documentation patches.",
                "Keep changes minimal.",
                "Never apply patches directly without approval.",
            ],
            expected_outputs=[
                "Patch proposal",
                "Unified diff patch",
                "Patch rationale",
                "Affected files",
            ],
            implemented_capabilities=[
                "Deterministic patch generator exists.",
                "Agno Dev Agent patch generation exists.",
                "Patch sanitizer exists.",
                "git apply --check validation exists.",
                "rejected.patch is saved for invalid patches.",
            ],
            future_capabilities=[
                "Autonomous patch loop after test failures.",
                "Better repository context selection.",
                "Multi-file implementation patch generation.",
            ],
        ),
        AgentRoleSpec(
            role_id="test_agent",
            display_name="Test Agent",
            purpose="Detect, run, summarize, and analyze tests safely.",
            responsibilities=[
                "Detect available test commands.",
                "Run allowlisted safe test commands.",
                "Summarize results.",
                "Identify likely cause of failures.",
                "Suggest next action if tests fail.",
            ],
            expected_outputs=[
                "Detected test command",
                "Test status",
                "Test summary",
                "Failure category",
                "Recommended next actions",
            ],
            implemented_capabilities=[
                "Test command detection exists.",
                "Safe test runner exists.",
                "Test result tracking exists.",
                "Test failure analysis exists.",
                "continue/auto-continue are test-aware.",
            ],
            future_capabilities=[
                "Targeted test selection.",
                "CI failure analysis.",
                "Automatic fix patch suggestion.",
            ],
        ),
        AgentRoleSpec(
            role_id="release_judge_agent",
            display_name="Release Judge Agent",
            purpose="Judge whether the work is ready for commit, push, PR, or final review.",
            responsibilities=[
                "Compare request, patch, tests, approvals, git state, and risks.",
                "Block unsafe progress.",
                "Prefer evidence over model opinion.",
                "Never approve risky actions silently.",
            ],
            expected_outputs=[
                "Readiness status",
                "Risk level",
                "Blockers",
                "Warnings",
                "Next actions",
            ],
            implemented_capabilities=[
                "readiness-check command exists.",
                "Policy profiles exist.",
                "Approval request details exist.",
                "Test failure state can block workflow.",
                "Production profile can block push/PR without readiness/tests.",
            ],
            future_capabilities=[
                "LLM-assisted release judgment.",
                "CI-aware readiness.",
                "Policy-profile specific release gates.",
            ],
        ),
    ]

    return {role.role_id: role for role in roles}


def get_agent_role_spec(role_id: str) -> AgentRoleSpec:
    roles = get_agent_role_specs()

    if role_id not in roles:
        allowed = ", ".join(sorted(roles.keys()))
        raise RuntimeError(f"Unknown agent role: {role_id}. Allowed: {allowed}")

    return roles[role_id]
