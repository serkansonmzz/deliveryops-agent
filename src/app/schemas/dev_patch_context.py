from pydantic import BaseModel, Field


class DevContextFile(BaseModel):
    path: str
    content: str
    reason: str
    kind: str = "unknown"


class DevPatchContext(BaseModel):
    request: str
    issue_url: str | None = None
    branch_name: str | None = None
    feature_title: str | None = None
    issue_title: str | None = None
    architecture_summary: str | None = None
    architecture_recommended_approach: list[str] = Field(default_factory=list)
    architecture_risks: list[str] = Field(default_factory=list)
    architecture_security_notes: list[str] = Field(default_factory=list)
    architecture_testing_notes: list[str] = Field(default_factory=list)
    architecture_devops_notes: list[str] = Field(default_factory=list)
    implementation_plan_summary: str | None = None
    implementation_plan_steps: list[dict] = Field(default_factory=list)
    implementation_target_files: list[str] = Field(default_factory=list)
    implementation_test_strategy: list[str] = Field(default_factory=list)
    implementation_risks: list[str] = Field(default_factory=list)
    selected_files: list[DevContextFile] = Field(default_factory=list)
    related_tests: list[str] = Field(default_factory=list)
    risky_files: list[str] = Field(default_factory=list)
    allowed_target_files: list[str] = Field(default_factory=list)
    blocked_file_patterns: list[str] = Field(default_factory=list)
    patch_rules: list[str] = Field(default_factory=list)
    policy_profile: str | None = None

    def as_prompt_text(self) -> str:
        file_sections: list[str] = []
        for file in self.selected_files:
            file_sections.append(
                "\n".join(
                    [
                        f"### File: {file.path}",
                        f"Kind: {file.kind}",
                        f"Reason: {file.reason}",
                        "",
                        "```",
                        file.content,
                        "```",
                    ]
                )
            )

        return "\n".join(
            [
                "## Request",
                self.request,
                "",
                "## Issue",
                f"Issue URL: {self.issue_url or 'not available'}",
                f"Issue Title: {self.issue_title or 'not available'}",
                "",
                "## Branch",
                self.branch_name or "not available",
                "",
                "## Feature",
                self.feature_title or "not available",
                "",
                "## Architecture Summary",
                self.architecture_summary or "not available",
                "",
                "## Architecture Recommended Approach",
                "\n".join(
                    f"- {item}" for item in self.architecture_recommended_approach
                )
                or "- none",
                "",
                "## Architecture Risks",
                "\n".join(f"- {item}" for item in self.architecture_risks)
                or "- none",
                "",
                "## Security Notes",
                "\n".join(f"- {item}" for item in self.architecture_security_notes)
                or "- none",
                "",
                "## Testing Notes",
                "\n".join(f"- {item}" for item in self.architecture_testing_notes)
                or "- none",
                "",
                "## DevOps Notes",
                "\n".join(f"- {item}" for item in self.architecture_devops_notes)
                or "- none",
                "",
                "## Implementation Plan Summary",
                self.implementation_plan_summary or "not available",
                "",
                "## Implementation Plan Steps",
                "\n".join(
                    f"- Step {step.get('step_number')}: {step.get('title')} - "
                    f"{step.get('description')}"
                    for step in self.implementation_plan_steps
                )
                or "- none",
                "",
                "## Implementation Target Files",
                "\n".join(f"- {item}" for item in self.implementation_target_files)
                or "- none",
                "",
                "## Related Tests",
                "\n".join(f"- {item}" for item in self.related_tests) or "- none",
                "",
                "## Risky Files",
                "\n".join(f"- {item}" for item in self.risky_files) or "- none",
                "",
                "## Allowed Target Files",
                "\n".join(f"- {item}" for item in self.allowed_target_files)
                or "- none",
                "",
                "## Blocked File Patterns",
                "\n".join(f"- {item}" for item in self.blocked_file_patterns)
                or "- none",
                "",
                "## Patch Rules",
                "\n".join(f"- {item}" for item in self.patch_rules) or "- none",
                "",
                "## Selected Repository Files",
                "\n\n".join(file_sections) or "No files selected.",
            ]
        )
