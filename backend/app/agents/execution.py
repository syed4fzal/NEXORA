"""
app/agents/execution.py
~~~~~~~~~~~~~~~~~~~~~~~

Local Tool Execution component for Nexora.

Executes a TaskPlan sequentially and routes data-analysis subtasks
to the correct specialized DataAnalyzer method.

Supported analysis routing:
- sales
- profit
- discount
- category
- region
- product
- loss-making transactions
- unusual values
- general statistical analysis

No LLM, external API, network access, or ML models are used.
"""

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from app.agents.planning import TaskPlan
from app.agents.tools.data_tools import (
    DataAnalyzer,
    DataInspector,
    DataLoader,
)

_DATA_FILE_PATH = "data/superstore.csv"


# ---------------------------------------------------------------------
# Execution Result
# ---------------------------------------------------------------------


@dataclass
class ToolExecutionResult:
    """The outcome of executing a single plan step."""

    step_number: int
    tool: str
    success: bool
    output: str


# ---------------------------------------------------------------------
# Tool Executor
# ---------------------------------------------------------------------


class ToolExecutor:
    """Executes a TaskPlan sequentially.

    The executor routes analysis requests to specialized deterministic
    DataAnalyzer methods based on the subtask description.
    """

    def __init__(self) -> None:

        self._data_loader = DataLoader()
        self._data_inspector = DataInspector()
        self._data_analyzer = DataAnalyzer()

        # Task-specific state.
        self._dataframe: pd.DataFrame | None = None

        # Stores the result returned by the specialized analyzer.
        self._analysis_result = None

        # Stores the original analysis request.
        self._analysis_request: str = ""

        self._tool_handlers: dict[str, Callable[[str], str]] = {
            "data_loader": self._run_data_loader,
            "data_inspector": self._run_data_inspector,
            "data_analyzer": self._run_data_analyzer,
            "document_reader": self._run_document_reader,
            "document_extractor": self._run_document_extractor,
            "document_summarizer": self._run_document_summarizer,
            "report_generator": self._run_report_generator,
            "general_processor": self._run_general_processor,
        }

    # ================================================================
    # MAIN EXECUTION
    # ================================================================

    def execute(
        self,
        plan: TaskPlan,
    ) -> list[ToolExecutionResult]:
        """Execute all steps in a TaskPlan."""

        # Reset task-specific state.
        self._dataframe = None
        self._analysis_result = None
        self._analysis_request = ""

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
                        f"Skipped: one or more dependencies for "
                        f"step {step.step_number} failed."
                    ),
                )

            else:
                result = self._execute_step(
                    step_number=step.step_number,
                    tool=step.tool,
                    description=step.description,
                )

            results.append(result)
            results_by_step[step.step_number] = result

        return results

    # ================================================================
    # DEPENDENCY HANDLING
    # ================================================================

    @staticmethod
    def _dependencies_succeeded(
        depends_on: list[int],
        results_by_step: dict[int, ToolExecutionResult],
    ) -> bool:
        """Return True when all dependencies succeeded."""

        for dependency_step in depends_on:

            dependency_result = results_by_step.get(
                dependency_step
            )

            if (
                dependency_result is None
                or not dependency_result.success
            ):
                return False

        return True

    # ================================================================
    # STEP EXECUTION
    # ================================================================

    def _execute_step(
        self,
        step_number: int,
        tool: str,
        description: str,
    ) -> ToolExecutionResult:
        """Execute one planned step."""

        handler = self._tool_handlers.get(tool)

        if handler is None:
            return ToolExecutionResult(
                step_number=step_number,
                tool=tool,
                success=False,
                output=f"Unknown tool: {tool}",
            )

        try:
            output = handler(description)

        except Exception as exc:

            return ToolExecutionResult(
                step_number=step_number,
                tool=tool,
                success=False,
                output=(
                    f"Execution failed for tool '{tool}': "
                    f"{exc}"
                ),
            )

        return ToolExecutionResult(
            step_number=step_number,
            tool=tool,
            success=True,
            output=output,
        )

    # ================================================================
    # DATA LOADER
    # ================================================================

    def _run_data_loader(
        self,
        description: str,
    ) -> str:
        """Load the Superstore dataset."""

        result = self._data_loader.load(
            _DATA_FILE_PATH
        )

        if not result.success:
            raise RuntimeError(
                f"Data loading failed: {result.error}"
            )

        self._dataframe = result.dataframe

        return (
            f"Loaded '{result.file_path}' successfully "
            f"({result.rows} rows, {result.columns} columns)."
        )

    # ================================================================
    # DATA INSPECTOR
    # ================================================================

    def _run_data_inspector(
        self,
        description: str,
    ) -> str:
        """Inspect the loaded dataset."""

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

        total_missing = sum(
            result.missing_value_counts.values()
        )

        columns_with_missing = [
            column
            for column, count
            in result.missing_value_counts.items()
            if count > 0
        ]

        if total_missing:
            missing_summary = (
                f"{total_missing} missing values across "
                f"{len(columns_with_missing)} column(s)"
            )
        else:
            missing_summary = "no missing values"

        return (
            f"Inspected dataset: "
            f"{result.row_count} rows, "
            f"{result.column_count} columns. "
            f"Numeric columns: "
            f"{', '.join(map(str, numeric_columns)) or 'none'}. "
            f"Missing values: {missing_summary}."
        )

    # ================================================================
    # SPECIALIZED DATA ANALYZER ROUTER
    # ================================================================

    def _run_data_analyzer(
        self,
        description: str,
    ) -> str:
        """Route the request to the appropriate DataAnalyzer method."""

        if self._dataframe is None:
            raise RuntimeError(
                "No dataframe has been loaded to analyze."
            )

        request = description.lower().strip()

        self._analysis_request = description

        # ------------------------------------------------------------
        # 1. Loss-making transactions
        # ------------------------------------------------------------

        if (
            "loss-making" in request
            or "loss making" in request
            or "loss-making transaction" in request
            or "loss making transaction" in request
        ):
            result = (
                self._data_analyzer
                .find_loss_making_transactions(
                    self._dataframe
                )
            )

            if not result.success:
                raise RuntimeError(
                    f"Loss analysis failed: {result.error}"
                )

            self._analysis_result = result

            return (
                "Loss-making transaction analysis complete. "
                f"Loss-making transactions: "
                f"{result.loss_making_transactions}, "
                f"Total Loss: {result.total_loss:.2f}, "
                f"Average Loss: {result.average_loss:.2f}, "
                f"Maximum Loss: {result.maximum_loss:.2f}."
            )

        # ------------------------------------------------------------
        # 2. Unusual values / outliers / anomalies
        # ------------------------------------------------------------

        if (
            "unusual" in request
            or "outlier" in request
            or "outliers" in request
            or "anomaly" in request
            or "anomalies" in request
        ):
            result = (
                self._data_analyzer
                .summarize_unusual_values(
                    self._dataframe
                )
            )

            if not result.success:
                raise RuntimeError(
                    f"Unusual-value analysis failed: "
                    f"{result.error}"
                )

            self._analysis_result = result

            by_column = ", ".join(
                f"{column}: {count}"
                for column, count
                in result.unusual_values_by_column.items()
            )

            return (
                "Unusual-value analysis complete. "
                f"Total unusual values: "
                f"{result.total_unusual_values}. "
                f"By column: {by_column or 'none'}."
            )

        # ------------------------------------------------------------
        # 3. Discount analysis
        # ------------------------------------------------------------

        if (
            "discount" in request
            or "discounts" in request
        ):
            result = (
                self._data_analyzer
                .analyze_discounts(
                    self._dataframe
                )
            )

            if not result.success:
                raise RuntimeError(
                    f"Discount analysis failed: {result.error}"
                )

            self._analysis_result = result

            return (
                "Discount analysis complete. "
                f"Average Discount: "
                f"{result.average_discount:.2%}, "
                f"Minimum Discount: "
                f"{result.minimum_discount:.2%}, "
                f"Maximum Discount: "
                f"{result.maximum_discount:.2%}, "
                f"High-discount transactions (>50%): "
                f"{result.high_discount_transactions}, "
                f"Very-high-discount transactions (>70%): "
                f"{result.very_high_discount_transactions}."
            )

        # ------------------------------------------------------------
        # 4. Region analysis
        # ------------------------------------------------------------

        if (
            "region" in request
            or "regional" in request
        ):
            result = (
                self._data_analyzer
                .analyze_regions(
                    self._dataframe
                )
            )

            if not result.success:
                raise RuntimeError(
                    f"Region analysis failed: {result.error}"
                )

            self._analysis_result = result

            return (
                "Regional sales and profit analysis complete. "
                f"Highest sales region: "
                f"{result.highest_sales_region}, "
                f"Lowest sales region: "
                f"{result.lowest_sales_region}, "
                f"Highest profit region: "
                f"{result.highest_profit_region}, "
                f"Lowest profit region: "
                f"{result.lowest_profit_region}."
            )

        # ------------------------------------------------------------
        # 5. Category analysis
        # ------------------------------------------------------------

        if (
            "category" in request
            or "categories" in request
        ):
            result = (
                self._data_analyzer
                .analyze_categories(
                    self._dataframe
                )
            )

            if not result.success:
                raise RuntimeError(
                    f"Category analysis failed: {result.error}"
                )

            self._analysis_result = result

            return (
                "Category sales and profit analysis complete. "
                f"Highest sales category: "
                f"{result.highest_sales_category}, "
                f"Lowest sales category: "
                f"{result.lowest_sales_category}, "
                f"Highest profit category: "
                f"{result.highest_profit_category}, "
                f"Lowest profit category: "
                f"{result.lowest_profit_category}."
            )

        # ------------------------------------------------------------
        # 6. Product analysis
        # ------------------------------------------------------------

        if (
            "product" in request
            or "products" in request
        ):
            result = (
                self._data_analyzer
                .analyze_products(
                    self._dataframe
                )
            )

            if not result.success:
                raise RuntimeError(
                    f"Product analysis failed: {result.error}"
                )

            self._analysis_result = result

            return (
                "Product sales and profit analysis complete. "
                f"Highest sales product: "
                f"{result.highest_sales_product}, "
                f"Highest profit product: "
                f"{result.highest_profit_product}, "
                f"Lowest profit product: "
                f"{result.lowest_profit_product}."
            )

        # ------------------------------------------------------------
        # 7. Profit analysis
        # ------------------------------------------------------------

        if (
            "profit" in request
            or "profits" in request
        ):
            result = (
                self._data_analyzer
                .analyze_profit(
                    self._dataframe
                )
            )

            if not result.success:
                raise RuntimeError(
                    f"Profit analysis failed: {result.error}"
                )

            self._analysis_result = result

            return (
                "Profit analysis complete. "
                f"Total Profit: "
                f"{result.total_profit:.2f}, "
                f"Average Profit: "
                f"{result.average_profit:.2f}, "
                f"Median Profit: "
                f"{result.median_profit:.2f}, "
                f"Minimum Profit: "
                f"{result.minimum_profit:.2f}, "
                f"Maximum Profit: "
                f"{result.maximum_profit:.2f}, "
                f"Loss-making transactions: "
                f"{result.loss_making_transactions}, "
                f"Profitable transactions: "
                f"{result.profitable_transactions}, "
                f"Profit Margin: "
                f"{result.profit_margin_percentage:.2f}%."
            )

        # ------------------------------------------------------------
        # 8. Sales analysis
        # ------------------------------------------------------------

        if (
            "sales" in request
            or "sale" in request
        ):
            result = (
                self._data_analyzer
                .analyze_sales(
                    self._dataframe
                )
            )

            if not result.success:
                raise RuntimeError(
                    f"Sales analysis failed: {result.error}"
                )

            self._analysis_result = result

            return (
                "Sales analysis complete. "
                f"Total Sales: "
                f"{result.total_sales:.2f}, "
                f"Average Sales: "
                f"{result.average_sales:.2f}, "
                f"Median Sales: "
                f"{result.median_sales:.2f}, "
                f"Minimum Sales: "
                f"{result.minimum_sales:.2f}, "
                f"Maximum Sales: "
                f"{result.maximum_sales:.2f}, "
                f"Total Quantity: "
                f"{result.total_quantity:.0f}."
            )

        # ------------------------------------------------------------
        # 9. Generic deterministic analysis
        # ------------------------------------------------------------

        result = self._data_analyzer.analyze(
            self._dataframe
        )

        if not result.success:
            raise RuntimeError(
                f"General data analysis failed: {result.error}"
            )

        self._analysis_result = result

        return (
            "General statistical analysis complete. "
            f"Numeric columns: "
            f"{', '.join(result.numeric_columns) or 'none'}. "
            f"IQR-flagged unusual values: "
            f"{len(result.unusual_values)}."
        )

    # ================================================================
    # REPORT GENERATOR
    # ================================================================

    def _run_report_generator(
        self,
        description: str,
    ) -> str:
        """Generate an intent-specific deterministic report."""

        if self._dataframe is None:
            raise RuntimeError(
                "No dataframe has been loaded for report generation."
            )

        if self._analysis_result is None:
            raise RuntimeError(
                "No analysis result is available for report generation."
            )

        dataframe = self._dataframe
        result = self._analysis_result

        lines: list[str] = [
            "NEXORA DATA ANALYSIS REPORT",
            "=" * 32,
            "",
            "REQUEST",
            self._analysis_request or "Data analysis",
            "",
            "DATASET",
            f"Rows analyzed: {len(dataframe):,}",
            f"Columns analyzed: {len(dataframe.columns):,}",
            "",
        ]

        # ------------------------------------------------------------
        # Loss report
        # ------------------------------------------------------------

        if hasattr(result, "top_loss_making_transactions"):

            lines.extend(
                [
                    "LOSS-MAKING TRANSACTION ANALYSIS",
                    f"Loss-making transactions: "
                    f"{result.loss_making_transactions:,}",
                    f"Total Loss: "
                    f"{result.total_loss:,.2f}",
                    f"Average Loss: "
                    f"{result.average_loss:,.2f}",
                    f"Maximum Loss: "
                    f"{result.maximum_loss:,.2f}",
                    "",
                    "TOP LOSS-MAKING TRANSACTIONS",
                ]
            )

            if result.top_loss_making_transactions:

                for index, record in enumerate(
                    result.top_loss_making_transactions,
                    start=1,
                ):

                    details = ", ".join(
                        f"{key}={value}"
                        for key, value in record.items()
                    )

                    lines.append(
                        f"{index}. {details}"
                    )

            else:
                lines.append(
                    "No loss-making transactions found."
                )

        # ------------------------------------------------------------
        # Unusual-value report
        # ------------------------------------------------------------

        elif hasattr(result, "unusual_values_by_column"):

            lines.extend(
                [
                    "UNUSUAL-VALUE ANALYSIS",
                    f"Total unusual values: "
                    f"{result.total_unusual_values:,}",
                    "",
                    "UNUSUAL VALUES BY COLUMN",
                ]
            )

            if result.unusual_values_by_column:

                for column, count in (
                    result.unusual_values_by_column.items()
                ):
                    lines.append(
                        f"- {column}: {count}"
                    )

            else:
                lines.append(
                    "No unusual values detected."
                )

            lines.extend(
                [
                    "",
                    "Method: IQR statistical rule.",
                ]
            )

        # ------------------------------------------------------------
        # Profit report
        # ------------------------------------------------------------

        elif hasattr(result, "profit_margin_percentage"):

            lines.extend(
                [
                    "PROFIT ANALYSIS",
                    f"Total Profit: "
                    f"{result.total_profit:,.2f}",
                    f"Average Profit: "
                    f"{result.average_profit:,.2f}",
                    f"Median Profit: "
                    f"{result.median_profit:,.2f}",
                    f"Minimum Profit: "
                    f"{result.minimum_profit:,.2f}",
                    f"Maximum Profit: "
                    f"{result.maximum_profit:,.2f}",
                    f"Loss-making transactions: "
                    f"{result.loss_making_transactions:,}",
                    f"Profitable transactions: "
                    f"{result.profitable_transactions:,}",
                    f"Profit Margin: "
                    f"{result.profit_margin_percentage:.2f}%",
                ]
            )

        # ------------------------------------------------------------
        # Discount report
        # ------------------------------------------------------------

        elif hasattr(result, "very_high_discount_transactions"):

            lines.extend(
                [
                    "DISCOUNT ANALYSIS",
                    f"Average Discount: "
                    f"{result.average_discount:.2%}",
                    f"Minimum Discount: "
                    f"{result.minimum_discount:.2%}",
                    f"Maximum Discount: "
                    f"{result.maximum_discount:.2%}",
                    f"High-discount transactions (>50%): "
                    f"{result.high_discount_transactions:,}",
                    f"Very-high-discount transactions (>70%): "
                    f"{result.very_high_discount_transactions:,}",
                ]
            )

        # ------------------------------------------------------------
        # Region report
        # ------------------------------------------------------------

        elif hasattr(result, "sales_by_region"):

            lines.extend(
                [
                    "REGIONAL ANALYSIS",
                    f"Highest Sales Region: "
                    f"{result.highest_sales_region}",
                    f"Lowest Sales Region: "
                    f"{result.lowest_sales_region}",
                    f"Highest Profit Region: "
                    f"{result.highest_profit_region}",
                    f"Lowest Profit Region: "
                    f"{result.lowest_profit_region}",
                    "",
                    "SALES BY REGION",
                ]
            )

            for region, value in (
                result.sales_by_region.items()
            ):
                lines.append(
                    f"- {region}: {value:,.2f}"
                )

            lines.append("")
            lines.append("PROFIT BY REGION")

            for region, value in (
                result.profit_by_region.items()
            ):
                lines.append(
                    f"- {region}: {value:,.2f}"
                )

        # ------------------------------------------------------------
        # Category report
        # ------------------------------------------------------------

        elif hasattr(result, "sales_by_category"):

            lines.extend(
                [
                    "CATEGORY ANALYSIS",
                    f"Highest Sales Category: "
                    f"{result.highest_sales_category}",
                    f"Lowest Sales Category: "
                    f"{result.lowest_sales_category}",
                    f"Highest Profit Category: "
                    f"{result.highest_profit_category}",
                    f"Lowest Profit Category: "
                    f"{result.lowest_profit_category}",
                    "",
                    "SALES BY CATEGORY",
                ]
            )

            for category, value in (
                result.sales_by_category.items()
            ):
                lines.append(
                    f"- {category}: {value:,.2f}"
                )

            lines.append("")
            lines.append("PROFIT BY CATEGORY")

            for category, value in (
                result.profit_by_category.items()
            ):
                lines.append(
                    f"- {category}: {value:,.2f}"
                )

        # ------------------------------------------------------------
        # Product report
        # ------------------------------------------------------------

        elif hasattr(result, "top_10_products_by_sales"):

            lines.extend(
                [
                    "PRODUCT ANALYSIS",
                    f"Highest Sales Product: "
                    f"{result.highest_sales_product}",
                    f"Highest Profit Product: "
                    f"{result.highest_profit_product}",
                    f"Lowest Profit Product: "
                    f"{result.lowest_profit_product}",
                    "",
                    "TOP 10 PRODUCTS BY SALES",
                ]
            )

            for product, value in (
                result.top_10_products_by_sales.items()
            ):
                lines.append(
                    f"- {product}: {value:,.2f}"
                )

            lines.append("")
            lines.append("TOP 10 PRODUCTS BY PROFIT")

            for product, value in (
                result.top_10_products_by_profit.items()
            ):
                lines.append(
                    f"- {product}: {value:,.2f}"
                )

            lines.append("")
            lines.append(
                "BOTTOM 10 PRODUCTS BY PROFIT"
            )

            for product, value in (
                result.bottom_10_products_by_profit.items()
            ):
                lines.append(
                    f"- {product}: {value:,.2f}"
                )

        # ------------------------------------------------------------
        # Sales report
        # ------------------------------------------------------------

        elif hasattr(result, "total_sales"):

            lines.extend(
                [
                    "SALES ANALYSIS",
                    f"Total Sales: "
                    f"{result.total_sales:,.2f}",
                    f"Average Sales: "
                    f"{result.average_sales:,.2f}",
                    f"Median Sales: "
                    f"{result.median_sales:,.2f}",
                    f"Minimum Sales: "
                    f"{result.minimum_sales:,.2f}",
                    f"Maximum Sales: "
                    f"{result.maximum_sales:,.2f}",
                    f"Total Quantity: "
                    f"{result.total_quantity:,.0f}",
                ]
            )

        # ------------------------------------------------------------
        # Generic analysis report
        # ------------------------------------------------------------

        else:

            lines.extend(
                [
                    "GENERAL STATISTICAL ANALYSIS",
                    f"Numeric columns: "
                    f"{', '.join(result.numeric_columns) or 'none'}",
                    f"IQR-flagged unusual values: "
                    f"{len(result.unusual_values):,}",
                ]
            )

        # ------------------------------------------------------------
        # Footer
        # ------------------------------------------------------------

        lines.extend(
            [
                "",
                "EXECUTION",
                "Analysis performed deterministically "
                "using local pandas-based tools.",
                "No LLM, external API, network access, "
                "or ML model was used.",
            ]
        )

        return "\n".join(lines)

    # ================================================================
    # PLACEHOLDER TOOLS
    # ================================================================

    @staticmethod
    def _run_document_reader(
        description: str,
    ) -> str:
        return "Document read successfully."

    @staticmethod
    def _run_document_extractor(
        description: str,
    ) -> str:
        return (
            "Important information extracted successfully."
        )

    @staticmethod
    def _run_document_summarizer(
        description: str,
    ) -> str:
        return "Document summarized successfully."

    @staticmethod
    def _run_general_processor(
        description: str,
    ) -> str:
        return (
            "General task processing completed successfully."
        )