from app.schemas.delivery_state import DeliveryState
from app.schemas.policy_profile import PolicyDecision, PolicyProfileName


VALID_POLICY_PROFILES = {
    "sandbox",
    "personal_repo",
    "production_repo",
}

SAFE_ACTIONS = {
    "detect_tests",
    "run_tests",
    "analyze_test_failure",
    "readiness_check",
    "generate_commit_message",
    "final_report",
    "comment_progress",
}

APPROVAL_REQUIRED_ACTIONS = {
    "apply_patch",
    "git_commit",
    "git_push",
    "create_draft_pull_request",
}

BLOCKED_ACTIONS = {
    "force_push",
    "delete_repository",
    "delete_branch",
    "push_to_main_or_master_directly",
    "modify_secrets",
    "production_deploy",
    "arbitrary_shell_command",
    "destructive_file_operations",
}

SAFE_AUTO_ACTIONS_BY_PROFILE = {
    "sandbox": {
        "detect_tests",
        "run_tests",
        "analyze_test_failure",
        "readiness_check",
        "generate_commit_message",
        "final_report",
    },
    "personal_repo": {
        "detect_tests",
        "run_tests",
        "analyze_test_failure",
        "readiness_check",
        "generate_commit_message",
        "final_report",
    },
    "production_repo": {
        "detect_tests",
        "run_tests",
        "analyze_test_failure",
        "readiness_check",
        "final_report",
    },
}


def normalize_policy_profile(profile: str | None) -> PolicyProfileName:
    if profile in VALID_POLICY_PROFILES:
        return profile  # type: ignore[return-value]

    return "personal_repo"


def validate_policy_profile(profile: str) -> PolicyProfileName:
    if profile not in VALID_POLICY_PROFILES:
        allowed = ", ".join(sorted(VALID_POLICY_PROFILES))
        raise RuntimeError(f"Unknown policy profile: {profile}. Allowed: {allowed}")

    return profile  # type: ignore[return-value]


def get_safe_auto_actions_for_profile(profile: str | None) -> set[str]:
    normalized = normalize_policy_profile(profile)
    return SAFE_AUTO_ACTIONS_BY_PROFILE[normalized]


def evaluate_policy_action(state: DeliveryState, action: str) -> PolicyDecision:
    profile = normalize_policy_profile(state.policy_profile)

    if action in BLOCKED_ACTIONS:
        return PolicyDecision(
            profile=profile,
            action=action,
            permission="blocked",
            reason=f"Action is blocked by policy: {action}.",
            blockers=[f"Blocked action: {action}"],
        )

    if profile == "production_repo":
        if action in {"git_push", "create_draft_pull_request"}:
            blockers: list[str] = []

            if state.readiness_status != "ready":
                blockers.append(
                    "Production policy requires release readiness status to be `ready`."
                )

            if state.test_status != "passed":
                blockers.append(
                    "Production policy requires tests to pass before push or draft PR."
                )

            if blockers:
                return PolicyDecision(
                    profile=profile,
                    action=action,
                    permission="blocked",
                    reason=f"Production policy blocked action: {action}.",
                    blockers=blockers,
                )

        if action == "git_commit" and state.test_status == "failed":
            return PolicyDecision(
                profile=profile,
                action=action,
                permission="blocked",
                reason="Production policy blocks commit while tests are failing.",
                blockers=["Tests are failing."],
            )

    if action in APPROVAL_REQUIRED_ACTIONS:
        return PolicyDecision(
            profile=profile,
            action=action,
            permission="approval_required",
            reason=f"Action requires explicit approval: {action}.",
        )

    if action in SAFE_ACTIONS:
        return PolicyDecision(
            profile=profile,
            action=action,
            permission="safe",
            reason=f"Action is safe under profile `{profile}`: {action}.",
        )

    return PolicyDecision(
        profile=profile,
        action=action,
        permission="approval_required",
        reason=f"Unknown action defaults to approval-required: {action}.",
        warnings=["Unknown policy action. Treating as approval-required."],
    )


def ensure_policy_allows_action(state: DeliveryState, action: str) -> PolicyDecision:
    decision = evaluate_policy_action(state, action)

    state.last_policy_decision = (
        f"{decision.profile}:{decision.action}:{decision.permission}"
    )
    state.policy_warnings = decision.warnings

    if decision.permission == "blocked":
        blockers = "\n".join(f"- {blocker}" for blocker in decision.blockers)
        raise RuntimeError(
            f"Policy blocked action `{action}` under profile `{decision.profile}`.\n"
            f"{blockers}"
        )

    return decision
