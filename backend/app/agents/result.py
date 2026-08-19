"""
app/agents/result.py
~~~~~~~~~~~~~~~~~~~~~
Local, deterministic Final Result component for Nexora.

Turns a VerificationResult and the underlying execution results into a
single AgentResult summarizing the outcome of an agent run. No tool
execution or API calls happen here, and this component is not yet
wired into NexoraAgent.
"""

from dataclasses import dataclass

from app.agents.execution import ToolExecutionResult
from app.agents.verification import VerificationResult


@dataclass
class AgentResult:
    """The final, summarized outcome of a Nexora agent run."""

    success: bool
    summary: str
    steps_completed: int
    steps_failed: int
    execution_results: list[ToolExecutionResult]


class ResultBuilder:
    """Builds the final AgentResult from a verification and its execution results.

    This is a placeholder for a future, more capable result-reporting
    system. It only formats what verification already determined -- it
    performs no tool execution and makes no API calls.
    """

    def build(
        self,
        verification: VerificationResult,
        execution_results: list[ToolExecutionResult],
    ) -> AgentResult:
        """Build the final AgentResult for an agent run.

        Args:
            verification: The VerificationResult produced by
                ResultVerifier.verify().
            execution_results: The original ToolExecutionResult objects
                the verification was based on.

        Returns:
            An AgentResult with `success` mirroring
            `verification.verified`, a human-readable `summary`,
            `steps_completed`/`steps_failed` taken from the
            verification, and the original `execution_results`
            preserved unchanged.
        """
        if verification.verified:
            summary = "Nexora completed the task successfully. All execution steps were verified."
        else:
            summary = (
                "Nexora could not fully complete the task because one or more "
                "execution steps failed."
            )

        return AgentResult(
            success=verification.verified,
            summary=summary,
            steps_completed=verification.successful_steps,
            steps_failed=verification.failed_steps,
            execution_results=execution_results,
        )