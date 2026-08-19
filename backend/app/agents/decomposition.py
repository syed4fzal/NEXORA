"""
app/agents/decomposition.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Local, deterministic Task Decomposition component for Nexora.

Takes the structured output of TaskUnderstanding and produces an ordered
list of subtasks (a plan). This component does not execute anything --
it only builds the plan/subtask list. No LLM or external calls are used.
"""

from app.agents.understanding import TaskUnderstandingResult


class TaskDecomposer:
    """A small, deterministic subtask planner.

    This is a placeholder for a future, more capable planning system.
    It builds subtask lists using simple rules keyed off `intent`, with
    `action` and `target` substituted into templated steps.
    """

    def decompose(self, understanding: TaskUnderstandingResult) -> list[str]:
        """Break a task's understanding down into an ordered subtask list.

        Args:
            understanding: The structured result produced by
                TaskUnderstanding.understand().

        Returns:
            An ordered list of human-readable subtask descriptions. This
            is only a plan -- no subtask is actually executed here.
        """
        if understanding.intent == "data_analysis":
            return self._decompose_data_analysis(understanding)

        if understanding.intent == "document":
            return self._decompose_document(understanding)

        return self._decompose_general(understanding)

    @staticmethod
    def _decompose_data_analysis(understanding: TaskUnderstandingResult) -> list[str]:
        """Build the subtask sequence for a data-analysis task."""
        target = understanding.target
        return [
            f"Load the {target}",
            f"Inspect the {target} data",
            f"{understanding.action.capitalize()} the {target} data for unusual transactions",
            "Prepare a summary of the findings",
        ]

    @staticmethod
    def _decompose_document(understanding: TaskUnderstandingResult) -> list[str]:
        """Build the subtask sequence for a document task."""
        target = understanding.target
        return [
            f"Read the {target}",
            "Extract the important information",
            f"{understanding.action.capitalize()} the {target}",
            "Prepare the final summary",
        ]

    @staticmethod
    def _decompose_general(understanding: TaskUnderstandingResult) -> list[str]:
        """Build a small, sensible subtask sequence for an unclassified task."""
        return [
            "Understand the requested task",
            f"{understanding.action.capitalize()} the task",
            "Prepare the result",
        ]