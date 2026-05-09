from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import time
from typing import TypeVar

from app.cli.common import console


T = TypeVar("T")


def run_with_heartbeat(message: str, fn: Callable[[], T]) -> T:
    console.print(f"[cyan]{message}[/cyan]")

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn)
    started_at = time.monotonic()

    try:
        if console.is_interactive:
            with console.status(f"{message} ...", spinner="dots") as status:
                while True:
                    try:
                        return future.result(timeout=5)
                    except FutureTimeoutError:
                        elapsed = int(time.monotonic() - started_at)
                        status.update(f"{message} ... still working, {elapsed}s elapsed")

        while True:
            try:
                return future.result(timeout=15)
            except FutureTimeoutError:
                elapsed = int(time.monotonic() - started_at)
                console.print(f"[cyan]Still waiting on {message}, {elapsed}s elapsed.[/cyan]")
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
