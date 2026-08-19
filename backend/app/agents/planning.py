"""
app/agents/planning.py
~~~~~~~~~~~~~~~~~~~~~~~
Local, deterministic Planning component for Nexora.

Takes the subtask list produced by TaskDecomposer and turns it into a
structured execution plan: a sequence of PlanStep objects with an
assigned (placeholder) tool name and a simple sequential dependency
chain. No tool is actually executed here -- this only builds the plan.
"""

from dataclasses import dataclass, field

# Ordered keyword -> tool rules. Order matters: more specific/earlier
# rules are checked first (e.g. "prepare" is checked before "summar" so
# "Prepare a summary of the findings" maps to report_generator rather
# than document_summarizer).
_TOOL_KEYWORD_RULES: list[tuple[str, str]] = [
    ("load", "data_loader"),
    ("inspect", "data_inspector"),
    ("analyz", "data_analyzer"),
    ("read", "document_reader"),
    ("extract", "document_extractor"),
    ("prepare", "report_generator"),
    ("summar", "document_summarizer"),
]

_DEFAULT_TOOL = "general_processor"


@dataclass
class PlanStep:
    """A single step in a Nexora execution plan."""

    step_number: int
    description: str
    tool: str
    depends_on: list[int] = field(default_factory=list)


@dataclass
class TaskPlan:
    """An ordered, structured execution plan built from subtasks."""

    steps: list[PlanStep]


class TaskPlanner:
    """A small, deterministic planner.

    This is a placeholder for a future, more capable planning system. It
    assigns each subtask a placeholder tool name using simple keyword
    rules, and chains steps together with a simple sequential dependency
    model (each step depends only on the step directly before it).
    """

    def create_plan(self, subtasks: list[str]) -> TaskPlan:
        """Turn a list of subtask descriptions into a structured plan.

        Args:
            subtasks: An ordered list of subtask descriptions, typically
                produced by TaskDecomposer.decompose().

        Returns:
            A TaskPlan containing one PlanStep per subtask, each assigned
            a placeholder tool and a sequential dependency on the step
            before it. No tool is executed -- this only builds the plan.
        """
        steps: list[PlanStep] = []
        for index, subtask in enumerate(subtasks):
            step_number = index + 1
            depends_on = [step_number - 1] if step_number > 1 else []
            steps.append(
                PlanStep(
                    step_number=step_number,
                    description=subtask,
                    tool=self._assign_tool(subtask),
                    depends_on=depends_on,
                )
            )
        return TaskPlan(steps=steps)

    @staticmethod
    def _assign_tool(subtask: str) -> str:
        """Assign a placeholder tool name to a subtask using keyword rules."""
        lowered = subtask.lower()
        for keyword, tool in _TOOL_KEYWORD_RULES:
            if keyword in lowered:
                return tool
        return _DEFAULT_TOOL