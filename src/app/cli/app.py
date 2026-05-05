import typer

from app.cli.agent_commands import register_agent_commands
from app.cli.approval_commands import register_approval_commands
from app.cli.git_delivery_commands import register_git_delivery_commands
from app.cli.github_commands import register_github_commands
from app.cli.patch_commands import register_patch_commands
from app.cli.policy_commands import register_policy_commands
from app.cli.release_commands import register_release_commands
from app.cli.test_commands import register_test_commands
from app.cli.workflow_commands import register_workflow_commands


app = typer.Typer(
    help="DeliveryOps Agent: an approval-gated software delivery workflow manager."
)


def register_commands() -> None:
    register_workflow_commands(app)
    register_approval_commands(app)
    register_patch_commands(app)
    register_test_commands(app)
    register_git_delivery_commands(app)
    register_github_commands(app)
    register_release_commands(app)
    register_policy_commands(app)
    register_agent_commands(app)


register_commands()
