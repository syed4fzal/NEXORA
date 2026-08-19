"""
app/agents/retry.py
~~~~~~~~~~~~~~~~~~~~
Local, deterministic retry handling for Nexora tool execution.

Wraps a tool operation (an `execute` callback) with a bounded retry
loop. This component does not execute any real tools itself and is not
yet wired into ToolExecutor or NexoraAgent.
"""

from dataclasses import dataclass
from typing import Callable

from app.agents.execution import ToolExecutionResult  # noqa: F401  (compatibility import)


@dataclass
class RetryResult:
    """The outcome of retrying a tool operation."""

    step_number: int
    tool: str
    success: bool
    output: str
    attempts: int


class RetryHandler:
    """Retries a tool operation up to a configurable number of times.

    `retry_limit` is the number of *additional* attempts allowed after
    the first one -- e.g. retry_limit=2 means: first attempt, retry #1,
    retry #2, for a maximum of 3 total attempts.
    """

    def __init__(self, retry_limit: int = 2) -> None:
        if retry_limit < 0:
            raise ValueError("retry_limit must be zero or a positive integer.")
        self.retry_limit = retry_limit

    def retry(
        self,
        step_number: int,
        tool: str,
        execute: Callable[[], str],
    ) -> RetryResult:
        """Attempt `execute`, retrying on failure up to `retry_limit` times.

        Args:
            step_number: The plan step number this operation belongs to.
            tool: The name of the tool being executed.
            execute: A zero-argument callable representing the tool
                operation. It should return the tool's output string on
                success, or raise an exception on failure.

        Returns:
            A RetryResult describing whether the operation ultimately
            succeeded, its output (or a safe failure message), and the
            actual number of attempts made. Raw exception details are
            never included in the output.
        """
        max_attempts = self.retry_limit + 1
        attempts_made = 0

        for attempt_number in range(1, max_attempts + 1):
            attempts_made = attempt_number
            try:
                output = execute()
            except Exception:
                if attempt_number == max_attempts:
                    break
                continue
            else:
                return RetryResult(
                    step_number=step_number,
                    tool=tool,
                    success=True,
                    output=output,
                    attempts=attempts_made,
                )

        return RetryResult(
            step_number=step_number,
            tool=tool,
            success=False,
            output=f"Tool execution failed after {attempts_made} attempts.",
            attempts=attempts_made,
        )