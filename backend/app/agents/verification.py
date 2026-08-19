"""
app/agents/verification.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Local, deterministic Result Verification component for Nexora.

Inspects a list of ToolExecutionResult objects and produces a summary
verdict on whether the overall execution succeeded. No tool execution
happens here, and this component is not yet wired into NexoraAgent.
"""

from dataclasses import dataclass

from app.agents.execution import ToolExecutionResult


@dataclass
class VerificationResult:
    """The overall verdict for a set of tool execution results."""

    verified: bool
    successful_steps: int
    failed_steps: int
    summary: str


class ResultVerifier:
    """Verifies a list of ToolExecutionResult objects.

    This is a placeholder for a future, more capable verification
    system. It only aggregates the `success` flags already present on
    each result -- it performs no actual tool execution or re-checking
    of tool output.
    """

    def verify(self, results: list[ToolExecutionResult]) -> VerificationResult:
        """Verify a list of execution results.

        Args:
            results: The ToolExecutionResult objects produced by
                ToolExecutor.execute() (or an equivalent source).

        Returns:
            A VerificationResult that is `verified=True` only when
            `results` is non-empty and every result succeeded;
            otherwise `verified=False`, with `summary` describing the
            outcome.
        """
        if not results:
            return VerificationResult(
                verified=False,
                successful_steps=0,
                failed_steps=0,
                summary="No execution results to verify.",
            )

        successful_steps = sum(1 for result in results if result.success)
        failed_steps = len(results) - successful_steps
        verified = failed_steps == 0

        if verified:
            summary = f"All {successful_steps} execution steps completed successfully."
        else:
            summary = (
                f"Execution verification failed: {successful_steps} steps succeeded "
                f"and {failed_steps} steps failed."
            )

        return VerificationResult(
            verified=verified,
            successful_steps=successful_steps,
            failed_steps=failed_steps,
            summary=summary,
        )