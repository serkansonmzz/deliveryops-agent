from pydantic import BaseModel


class CommandResult(BaseModel):
    args: list[str]
    return_code: int
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.return_code == 0

    @property
    def combined_output(self) -> str:
        return "\n".join(
            part for part in [self.stdout, self.stderr] if part.strip()
        )
