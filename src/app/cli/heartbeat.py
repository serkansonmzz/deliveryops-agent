from collections.abc import Callable
from typing import TypeVar

from app.cli.common import console


T = TypeVar("T")


def run_with_heartbeat(message: str, fn: Callable[[], T]) -> T:
    console.print(f"[cyan]{message}[/cyan]")

    if console.is_interactive:
        with console.status(f"{message} ...", spinner="dots"):
            return fn()

    return fn()
