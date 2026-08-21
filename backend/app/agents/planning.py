"""
app/agents/planning.py
~~~~~~~~~~~~~~~~~~~~~~~

Local, deterministic Planning component for Nexora.

Takes the subtask list produced by TaskDecomposer and turns it into a
structured execution plan.

Phase 6 improvements:
- Better recognition of data-analysis subtasks.
- Preserves target-specific analysis requests.
- Supports analyze/analyse/find/review/inspect/examine/evaluate/
  identify/detect actions.
- Supports sales, profit, discount, transaction, product, category,
  regional, performance, loss, and unusual-value analysis.
- Correctly assigns report-generation subtasks to report_generator.
- Existing Phase 5 tools remain fully compatible.
- No LLM, external API, network access, or ML models are used.
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------
# Keyword -> tool rules
# ---------------------------------------------------------------------
#
# Rules are checked from top to bottom.
# More specific rules MUST appear before generic rules.
# ---------------------------------------------------------------------

_TOOL_KEYWORD_RULES: list[tuple[str, str]] = [

    # -------------------------------------------------------------
    # Data loading
    # -------------------------------------------------------------
    ("load dataset", "data_loader"),
    ("load data", "data_loader"),
    ("read csv", "data_loader"),
    ("read data", "data_loader"),
    ("import data", "data_loader"),
    ("import dataset", "data_loader"),
    ("load", "data_loader"),
    ("import", "data_loader"),

    # -------------------------------------------------------------
    # Data inspection
    # -------------------------------------------------------------
    ("inspect dataset", "data_inspector"),
    ("inspect data", "data_inspector"),
    ("inspect", "data_inspector"),
    ("structure", "data_inspector"),
    ("columns", "data_inspector"),
    ("missing values", "data_inspector"),
    ("missing value", "data_inspector"),
    ("dataset information", "data_inspector"),

    # -------------------------------------------------------------
    # Report generation
    # -------------------------------------------------------------
    #
    # IMPORTANT:
    # These rules MUST come before the generic "analysis" rule.
    # Otherwise "analysis" in "Generate the analysis report"
    # would incorrectly select data_analyzer.
    # -------------------------------------------------------------
    ("generate the analysis report", "report_generator"),
    ("generate analysis report", "report_generator"),
    ("generate the report", "report_generator"),
    ("generate report", "report_generator"),
    ("create the analysis report", "report_generator"),
    ("create analysis report", "report_generator"),
    ("create report", "report_generator"),
    ("prepare the analysis report", "report_generator"),
    ("prepare analysis report", "report_generator"),
    ("prepare the report", "report_generator"),
    ("prepare report", "report_generator"),
    ("prepare the final summary", "report_generator"),
    ("generate summary", "report_generator"),
    ("create summary", "report_generator"),
    ("final report", "report_generator"),
    ("analysis report", "report_generator"),
    ("report", "report_generator"),
    ("findings", "report_generator"),
    ("recommendation", "report_generator"),
    ("recommendations", "report_generator"),

    # -------------------------------------------------------------
    # Explicit data-analysis actions
    # -------------------------------------------------------------
    #
    # These are checked after report-generation rules so that
    # target-specific report subtasks are not misclassified.
    # -------------------------------------------------------------
    ("analyze", "data_analyzer"),
    ("analyse", "data_analyzer"),
    ("analysis", "data_analyzer"),
    ("find", "data_analyzer"),
    ("review", "data_analyzer"),
    ("examine", "data_analyzer"),
    ("evaluate", "data_analyzer"),
    ("identify", "data_analyzer"),
    ("detect", "data_analyzer"),

    # -------------------------------------------------------------
    # Data-analysis terminology
    # -------------------------------------------------------------
    ("statistics", "data_analyzer"),
    ("statistical", "data_analyzer"),

    ("sales", "data_analyzer"),
    ("sale", "data_analyzer"),

    ("profit", "data_analyzer"),
    ("profits", "data_analyzer"),

    ("revenue", "data_analyzer"),

    ("discount", "data_analyzer"),
    ("discounts", "data_analyzer"),

    ("transaction", "data_analyzer"),
    ("transactions", "data_analyzer"),

    ("unusual", "data_analyzer"),
    ("outlier", "data_analyzer"),
    ("outliers", "data_analyzer"),
    ("anomaly", "data_analyzer"),
    ("anomalies", "data_analyzer"),

    ("loss", "data_analyzer"),
    ("losses", "data_analyzer"),
    ("loss-making", "data_analyzer"),

    ("performance", "data_analyzer"),

    ("product", "data_analyzer"),
    ("products", "data_analyzer"),

    ("category", "data_analyzer"),
    ("categories", "data_analyzer"),

    ("region", "data_analyzer"),
    ("regions", "data_analyzer"),
    ("regional", "data_analyzer"),

    # -------------------------------------------------------------
    # Document tools
    # -------------------------------------------------------------
    ("read document", "document_reader"),
    ("read file", "document_reader"),
    ("extract", "document_extractor"),

    # -------------------------------------------------------------
    # Document summarization
    # -------------------------------------------------------------
    ("summarize", "document_summarizer"),
    ("summarise", "document_summarizer"),
    ("summar", "document_summarizer"),
]


_DEFAULT_TOOL = "general_processor"


# ---------------------------------------------------------------------
# Plan models
# ---------------------------------------------------------------------


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


# ---------------------------------------------------------------------
# Task Planner
# ---------------------------------------------------------------------


class TaskPlanner:
    """Deterministic planner for Nexora.

    Converts subtasks into executable tool steps.

    Each step depends on the immediately preceding step. This preserves
    the sequential execution behavior established in Phase 5.
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

        Rules are evaluated from top to bottom. More specific
        phrases must therefore appear before generic keywords.
        """

        lowered = subtask.lower().strip()

        for keyword, tool in _TOOL_KEYWORD_RULES:

            if keyword in lowered:
                return tool

        return _DEFAULT_TOOL