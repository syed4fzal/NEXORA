"""
app/agents/planning.py
~~~~~~~~~~~~~~~~~~~~~~~

Local, deterministic Planning component for Nexora.

Takes the subtask list produced by TaskDecomposer and turns it into a
structured execution plan.

Phase 6 improvements:
- Better recognition of data-analysis subtasks.
- More flexible keyword matching.
- Support for sales, profit, discount, transaction, product,
  category, and regional analysis requests.
- Existing Phase 5 tools remain fully compatible.
- No LLM, external API, network access, or ML models are used.
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------
# Keyword -> tool rules
# ---------------------------------------------------------------------
#
# Order matters.
#
# More specific rules should appear before generic rules.
#
# Example:
# "prepare a summary of the findings"
# should use report_generator rather than document_summarizer.
#

_TOOL_KEYWORD_RULES: list[tuple[str, str]] = [

    # -------------------------------------------------------------
    # Data loading
    # -------------------------------------------------------------
    ("load", "data_loader"),
    ("import", "data_loader"),
    ("read csv", "data_loader"),
    ("read data", "data_loader"),
    ("load data", "data_loader"),
    ("load dataset", "data_loader"),

    # -------------------------------------------------------------
    # Data inspection
    # -------------------------------------------------------------
    ("inspect", "data_inspector"),
    ("structure", "data_inspector"),
    ("columns", "data_inspector"),
    ("missing values", "data_inspector"),
    ("missing value", "data_inspector"),
    ("dataset information", "data_inspector"),

    # -------------------------------------------------------------
    # Data analysis
    # -------------------------------------------------------------
    ("analyz", "data_analyzer"),
    ("analyse", "data_analyzer"),
    ("analysis", "data_analyzer"),
    ("statistics", "data_analyzer"),
    ("statistical", "data_analyzer"),
    ("sales", "data_analyzer"),
    ("profit", "data_analyzer"),
    ("revenue", "data_analyzer"),
    ("discount", "data_analyzer"),
    ("transaction", "data_analyzer"),
    ("transactions", "data_analyzer"),
    ("unusual", "data_analyzer"),
    ("outlier", "data_analyzer"),
    ("outliers", "data_analyzer"),
    ("loss", "data_analyzer"),
    ("loss-making", "data_analyzer"),
    ("performance", "data_analyzer"),
    ("product", "data_analyzer"),
    ("products", "data_analyzer"),
    ("category", "data_analyzer"),
    ("categories", "data_analyzer"),
    ("region", "data_analyzer"),
    ("regional", "data_analyzer"),

    # -------------------------------------------------------------
    # Document tools
    # -------------------------------------------------------------
    ("read document", "document_reader"),
    ("read file", "document_reader"),
    ("extract", "document_extractor"),

    # -------------------------------------------------------------
    # Report generation
    # -------------------------------------------------------------
    ("prepare", "report_generator"),
    ("report", "report_generator"),
    ("generate report", "report_generator"),
    ("create report", "report_generator"),
    ("findings", "report_generator"),
    ("recommendation", "report_generator"),
    ("recommendations", "report_generator"),

    # -------------------------------------------------------------
    # Document summarization
    # -------------------------------------------------------------
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
    """Deterministic planner for Nexora.

    The planner converts subtasks into executable tool steps.

    Each step currently depends on the immediately preceding step.
    This preserves the execution behavior established in Phase 5.
    """

    def create_plan(
        self,
        subtasks: list[str],
    ) -> TaskPlan:
        """Turn subtasks into a structured execution plan.

        Args:
            subtasks:
                Ordered list of subtask descriptions produced by
                TaskDecomposer.

        Returns:
            TaskPlan containing one PlanStep for each subtask.
        """

        steps: list[PlanStep] = []

        for index, subtask in enumerate(subtasks):

            step_number = index + 1

            depends_on = (
                [step_number - 1]
                if step_number > 1
                else []
            )

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
    def _assign_tool(
        subtask: str,
    ) -> str:
        """Assign the most appropriate tool to a subtask.

        Matching is deterministic and case-insensitive.
        """

        lowered = subtask.lower().strip()

        for keyword, tool in _TOOL_KEYWORD_RULES:

            if keyword in lowered:
                return tool

        return _DEFAULT_TOOL

