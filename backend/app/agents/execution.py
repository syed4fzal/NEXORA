"""
app/agents/execution.py
~~~~~~~~~~~~~~~~~~~~~~~~
Local Tool Execution component for Nexora.

Executes a TaskPlan's steps sequentially. The data_loader,
data_inspector, and data_analyzer tools perform REAL, deterministic
work against the Superstore dataset using pandas.

The report_generator now also performs REAL deterministic work by
building a human-readable report from the loaded dataset and analysis.

No LLM, no external API, no network access, and no ML models are used
anywhere in this file.
"""

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from app.agents.planning import TaskPlan
from app.agents.tools.data_tools import DataAnalyzer, DataInspector, DataLoader

_DATA_FILE_PATH = "data/superstore.csv"


@dataclass
class ToolExecutionResult:
    """The outcome of executing a single plan step."""

    step_number: int
    tool: str
    success: bool
    output: str


class ToolExecutor:
    """Executes a TaskPlan's steps sequentially.

    Data tools perform real work against the Superstore dataset.

    The DataFrame and analysis result are kept only for the duration
    of one execute() call. They are reset at the beginning of every
    execution so data from one task cannot leak into another task.
    """

    def __init__(self) -> None:
        self._data_loader = DataLoader()
        self._data_inspector = DataInspector()
        self._data_analyzer = DataAnalyzer()

        self._dataframe: pd.DataFrame | None = None
        self._analysis_result = None

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
        """Execute a plan's steps in order while respecting dependencies."""

        # Reset task-specific state.
        self._dataframe = None
        self._analysis_result = None

        results_by_step: dict[int, ToolExecutionResult] = {}
        results: list[ToolExecutionResult] = []

        for step in plan.steps:
            if not self._dependencies_succeeded(
                step.depends_on,
                results_by_step,
            ):
                result = ToolExecutionResult(
                    step_number=step.step_number,
                    tool=step.tool,
                    success=False,
                    output=(
                        f"Skipped: one or more dependencies for step "
                        f"{step.step_number} did not complete successfully."
                    ),
                )
            else:
                result = self._execute_step(
                    step.step_number,
                    step.tool,
                )

            results.append(result)
            results_by_step[step.step_number] = result

        return results

    @staticmethod
    def _dependencies_succeeded(
        depends_on: list[int],
        results_by_step: dict[int, ToolExecutionResult],
    ) -> bool:
        """Return True if every dependency completed successfully."""

        for dependency_step in depends_on:
            dependency_result = results_by_step.get(dependency_step)

            if dependency_result is None or not dependency_result.success:
                return False

        return True

    def _execute_step(
        self,
        step_number: int,
        tool: str,
    ) -> ToolExecutionResult:
        """Run a single tool handler safely."""

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

    # ================================================================
    # REAL DATA TOOLS
    # ================================================================

    def _run_data_loader(self) -> str:
        """Load the Superstore dataset."""

        result = self._data_loader.load(_DATA_FILE_PATH)

        if not result.success:
            raise RuntimeError(
                f"Data loading failed: {result.error}"
            )

        self._dataframe = result.dataframe

        return (
            f"Loaded '{result.file_path}' successfully "
            f"({result.rows} rows, {result.columns} columns)."
        )

    def _run_data_inspector(self) -> str:
        """Inspect the loaded Superstore dataset."""

        if self._dataframe is None:
            raise RuntimeError(
                "No dataframe has been loaded to inspect."
            )

        result = self._data_inspector.inspect(
            self._dataframe
        )

        if not result.success:
            raise RuntimeError(
                f"Data inspection failed: {result.error}"
            )

        numeric_columns = list(
            self._dataframe.select_dtypes(
                include="number"
            ).columns
        )

        columns_with_missing = [
            column
            for column, count in result.missing_value_counts.items()
            if count > 0
        ]

        total_missing = sum(
            result.missing_value_counts.values()
        )

        if total_missing > 0:
            missing_summary = (
                f"{total_missing} missing values across "
                f"{len(columns_with_missing)} column(s)"
            )
        else:
            missing_summary = "no missing values"

        return (
            f"Inspected dataset: {result.row_count} rows, "
            f"{result.column_count} columns. "
            f"Numeric columns: "
            f"{', '.join(map(str, numeric_columns)) or 'none'}. "
            f"Missing values: {missing_summary}."
        )

    def _run_data_analyzer(self) -> str:
        """Run statistical analysis on the loaded dataset."""

        if self._dataframe is None:
            raise RuntimeError(
                "No dataframe has been loaded to analyze."
            )

        result = self._data_analyzer.analyze(
            self._dataframe
        )

        if not result.success:
            raise RuntimeError(
                f"Data analysis failed: {result.error}"
            )

        # Keep the complete analysis result for report generation.
        self._analysis_result = result

        try:
            total_sales = float(
                self._dataframe["Sales"].sum()
            )

            average_sales = float(
                self._dataframe["Sales"].mean()
            )

            total_profit = float(
                self._dataframe["Profit"].sum()
            )

            average_profit = float(
                self._dataframe["Profit"].mean()
            )

            total_quantity = float(
                self._dataframe["Quantity"].sum()
            )

            average_discount = float(
                self._dataframe["Discount"].mean()
            )

            loss_making_transactions = int(
                (self._dataframe["Profit"] < 0).sum()
            )

            high_discount_transactions = int(
                (self._dataframe["Discount"] > 0.5).sum()
            )

        except KeyError as exc:
            raise RuntimeError(
                f"Expected column missing from dataset: {exc}"
            ) from exc

        unusual_value_count = len(
            result.unusual_values
        )

        return (
            f"Analysis complete. "
            f"Total Sales: {total_sales:.2f}, "
            f"Average Sales: {average_sales:.2f}, "
            f"Total Profit: {total_profit:.2f}, "
            f"Average Profit: {average_profit:.2f}, "
            f"Total Quantity: {total_quantity:.0f}, "
            f"Average Discount: {average_discount:.4f}, "
            f"Loss-making transactions: "
            f"{loss_making_transactions}, "
            f"High-discount transactions (>0.5): "
            f"{high_discount_transactions}, "
            f"IQR-flagged unusual values: "
            f"{unusual_value_count}."
        )

    # ================================================================
    # REAL REPORT GENERATOR
    # ================================================================

    def _run_report_generator(self) -> str:
        """Generate a human-readable report from the analyzed dataset."""

        if self._dataframe is None:
            raise RuntimeError(
                "No dataframe has been loaded for report generation."
            )

        if self._analysis_result is None:
            raise RuntimeError(
                "No analysis result is available for report generation."
            )

        dataframe = self._dataframe
        analysis = self._analysis_result

        try:
            total_sales = float(
                dataframe["Sales"].sum()
            )

            average_sales = float(
                dataframe["Sales"].mean()
            )

            total_profit = float(
                dataframe["Profit"].sum()
            )

            average_profit = float(
                dataframe["Profit"].mean()
            )

            total_quantity = int(
                dataframe["Quantity"].sum()
            )

            average_discount = float(
                dataframe["Discount"].mean()
            )

            loss_making_transactions = int(
                (dataframe["Profit"] < 0).sum()
            )

            high_discount_transactions = int(
                (dataframe["Discount"] > 0.5).sum()
            )

        except KeyError as exc:
            raise RuntimeError(
                f"Expected column missing for report: {exc}"
            ) from exc

        unusual_count = len(
            analysis.unusual_values
        )

        # ------------------------------------------------------------
        # Automatic findings
        # ------------------------------------------------------------

        findings: list[str] = []

        if total_profit > 0:
            findings.append(
                f"The dataset generated a positive total profit "
                f"of {total_profit:.2f}."
            )
        else:
            findings.append(
                f"The dataset generated a negative total profit "
                f"of {total_profit:.2f}."
            )

        if loss_making_transactions > 0:
            findings.append(
                f"{loss_making_transactions} transactions "
                f"recorded a negative profit."
            )

        if high_discount_transactions > 0:
            findings.append(
                f"{high_discount_transactions} transactions "
                f"used a discount greater than 50%."
            )

        if unusual_count > 0:
            findings.append(
                f"{unusual_count} numeric values were flagged "
                f"as unusual using the IQR statistical rule."
            )

        if average_discount > 0.20:
            findings.append(
                "The average discount is relatively high "
                "at more than 20%."
            )
        else:
            findings.append(
                "The average discount is below 20%."
            )

        # ------------------------------------------------------------
        # Report
        # ------------------------------------------------------------

        report_lines = [
            "NEXORA DATA ANALYSIS REPORT",
            "=" * 32,
            "",
            "DATASET",
            f"Rows analyzed: {len(dataframe):,}",
            f"Columns analyzed: {len(dataframe.columns):,}",
            "",
            "SALES",
            f"Total Sales: {total_sales:,.2f}",
            f"Average Sales: {average_sales:,.2f}",
            "",
            "PROFIT",
            f"Total Profit: {total_profit:,.2f}",
            f"Average Profit: {average_profit:,.2f}",
            f"Loss-making transactions: "
            f"{loss_making_transactions:,}",
            "",
            "QUANTITY",
            f"Total Quantity: {total_quantity:,}",
            "",
            "DISCOUNT",
            f"Average Discount: "
            f"{average_discount:.2%}",
            f"High-discount transactions (>50%): "
            f"{high_discount_transactions:,}",
            "",
            "UNUSUAL VALUES",
            f"IQR-flagged unusual values: "
            f"{unusual_count:,}",
            "",
            "KEY FINDINGS",
        ]

        for index, finding in enumerate(findings, start=1):
            report_lines.append(
                f"{index}. {finding}"
            )

        report_lines.extend(
            [
                "",
                "Analysis method: deterministic statistical "
                "analysis using pandas and the IQR rule.",
                "No LLM, external API, network access, or ML "
                "model was used.",
            ]
        )

        return "\n".join(report_lines)

    # ================================================================
    # PLACEHOLDER TOOLS
    # ================================================================

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
    def _run_general_processor() -> str:
        return "General task processing completed successfully."

