"""
app/agents/execution.py
~~~~~~~~~~~~~~~~~~~~~~~~
Local Tool Execution component for Nexora.

Executes a TaskPlan's steps sequentially using local placeholder tool
implementations. No real files are read, no network/API calls are made,
and no actual data analysis is performed -- each "tool" simply returns
a canned success message. This component is not yet wired into
NexoraAgent.
"""

from dataclasses import dataclass
from typing import Callable

from app.agents.planning import TaskPlan


@dataclass
class ToolExecutionResult:
    """The outcome of executing a single plan step."""

    step_number: int
    tool: str
    success: bool
    output: str


class ToolExecutor:
    """Executes a TaskPlan's steps sequentially using placeholder tools.

    This is a placeholder for a future, more capable execution engine.
    Dependencies are respected: a step only runs if every step listed in
    its `depends_on` has already completed successfully. Unknown tools
    and exceptions during execution produce a failed result rather than
    crashing the executor.
    """

    def __init__(self) -> None:
        self._tool_handlers: dict[str, Callable[[], str]] = {
            "data_loader": self._run_data_loader,
            "data_inspector": self._run_data_inspector,
            "data_analyzer": self._run_data_analyzer,
            "document_reader": self._run_document_reader,
            "document_extractor": self._run_document_extractor,
            "document_summarizer": self._run_document_summarizer,
            "report_generator": self._run_report_generator,
            "general_processor": self._run_general_processor,
        }

    def execute(self, plan: TaskPlan) -> list[ToolExecutionResult]:
        """Execute a plan's steps in order, respecting dependencies.

        Args:
            plan: A TaskPlan produced by TaskPlanner.create_plan().

        Returns:
            One ToolExecutionResult per step, in step order. A step
            whose dependencies did not all succeed is not executed and
            is recorded as a failure; an unknown tool or a raised
            exception also produces a failure rather than stopping the
            whole run.
        """
        results_by_step: dict[int, ToolExecutionResult] = {}
        results: list[ToolExecutionResult] = []

        for step in plan.steps:
            if not self._dependencies_succeeded(step.depends_on, results_by_step):
                result = ToolExecutionResult(
                    step_number=step.step_number,
                    tool=step.tool,
                    success=False,
                    output=(
                        f"Skipped: one or more dependencies for step {step.step_number} "
                        "did not complete successfully."
                    ),
                )
            else:
                result = self._execute_step(step.step_number, step.tool)

            results.append(result)
            results_by_step[step.step_number] = result

        return results

    @staticmethod
    def _dependencies_succeeded(
        depends_on: list[int], results_by_step: dict[int, ToolExecutionResult]
    ) -> bool:
        """Return True if every dependency completed with success=True."""
        for dependency_step in depends_on:
            dependency_result = results_by_step.get(dependency_step)
            if dependency_result is None or not dependency_result.success:
                return False
        return True

    def _execute_step(self, step_number: int, tool: str) -> ToolExecutionResult:
        """Run a single step's tool handler, catching errors safely."""
        handler = self._tool_handlers.get(tool)

        if handler is None:
            return ToolExecutionResult(
                step_number=step_number,
                tool=tool,
                success=False,
                output=f"Unknown tool: {tool}",
            )

        try:
            output = handler()
        except Exception:
            return ToolExecutionResult(
                step_number=step_number,
                tool=tool,
                success=False,
                output=f"Execution failed for tool '{tool}'.",
            )

        return ToolExecutionResult(
            step_number=step_number,
            tool=tool,
            success=True,
            output=output,
        )

    # --- Placeholder tool implementations ---
    # These perform no real work: no file I/O, no network access, no
    # actual data analysis. Each simply returns a canned success message.

    @staticmethod
    def _run_data_loader() -> str:
        return "Loaded data successfully."

    @staticmethod
    def _run_data_inspector() -> str:
        return "Data inspection completed successfully."

    @staticmethod
    def _run_data_analyzer() -> str:
        return "Data analysis completed successfully."

    @staticmethod
    def _run_document_reader() -> str:
        return "Document read successfully."

    @staticmethod
    def _run_document_extractor() -> str:
        return "Important information extracted successfully."

    @staticmethod
    def _run_document_summarizer() -> str:
        return "Document summarized successfully."

    @staticmethod
    def _run_report_generator() -> str:
        return "Report generated successfully."

    @staticmethod
    def _run_general_processor() -> str:
        return "General task processing completed successfully."