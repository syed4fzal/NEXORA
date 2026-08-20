"""
app/agents/tools/data_tools.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Local, deterministic data-handling tools for Nexora.

Supports:
- CSV loading
- Excel loading
- Dataset inspection
- Sales/profit/discount/quantity analysis
- IQR-based unusual-value detection

No network access, no LLM, and no ML models are used here.
"""

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


_SUPPORTED_CSV_EXTENSIONS = {".csv"}
_SUPPORTED_EXCEL_EXTENSIONS = {".xlsx", ".xls"}

# Business metrics that Nexora should analyze for sales datasets.
_BUSINESS_NUMERIC_COLUMNS = {
    "Sales",
    "Profit",
    "Discount",
    "Quantity",
}


@dataclass
class DataLoadResult:
    """The outcome of attempting to load a data file."""

    success: bool
    file_path: str
    rows: int
    columns: int
    error: str | None = None
    dataframe: pd.DataFrame | None = field(default=None, repr=False)


@dataclass
class DataInspectionResult:
    """A structural summary of a loaded dataset."""

    success: bool
    row_count: int
    column_count: int
    column_names: list[str]
    dtypes: dict[str, str]
    missing_value_counts: dict[str, int]
    error: str | None = None


@dataclass
class ColumnStatistics:
    """Basic descriptive statistics for a numeric business column."""

    column: str
    count: int
    mean: float
    std: float
    min: float
    max: float
    median: float


@dataclass
class UnusualValue:
    """A single value flagged by the IQR outlier check."""

    column: str
    row_index: int
    value: float


@dataclass
class DataAnalysisResult:
    """The outcome of running business-oriented statistical analysis."""

    success: bool
    numeric_columns: list[str]
    statistics: list[ColumnStatistics]
    unusual_values: list[UnusualValue]

    total_sales: float = 0.0
    average_sales: float = 0.0

    total_profit: float = 0.0
    average_profit: float = 0.0

    total_quantity: int = 0
    average_quantity: float = 0.0

    average_discount: float = 0.0

    loss_making_transactions: int = 0
    high_discount_transactions: int = 0

    error: str | None = None


class DataLoader:
    """Loads CSV or Excel files into pandas DataFrames."""

    def load(self, file_path: str) -> DataLoadResult:
        """Load a CSV or Excel file from disk."""

        path = Path(file_path)

        if not path.exists():
            return DataLoadResult(
                success=False,
                file_path=file_path,
                rows=0,
                columns=0,
                error=f"File not found: {file_path}",
            )

        if not path.is_file():
            return DataLoadResult(
                success=False,
                file_path=file_path,
                rows=0,
                columns=0,
                error=f"Path is not a file: {file_path}",
            )

        extension = path.suffix.lower()

        try:
            if extension in _SUPPORTED_CSV_EXTENSIONS:
                dataframe = self._load_csv(path)

            elif extension in _SUPPORTED_EXCEL_EXTENSIONS:
                dataframe = pd.read_excel(
                    path,
                    engine="openpyxl" if extension == ".xlsx" else None,
                )

            else:
                return DataLoadResult(
                    success=False,
                    file_path=file_path,
                    rows=0,
                    columns=0,
                    error=(
                        f"Unsupported file extension: "
                        f"{extension or '(none)'}"
                    ),
                )

        except Exception as exc:
            return DataLoadResult(
                success=False,
                file_path=file_path,
                rows=0,
                columns=0,
                error=f"Failed to read file: {exc.__class__.__name__}",
            )

        rows, columns = dataframe.shape

        return DataLoadResult(
            success=True,
            file_path=file_path,
            rows=rows,
            columns=columns,
            dataframe=dataframe,
        )

    @staticmethod
    def _load_csv(path: Path) -> pd.DataFrame:
        """Load CSV using UTF-8 first, then latin1 if required."""

        try:
            return pd.read_csv(path, encoding="utf-8")

        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="latin1")


class DataInspector:
    """Reports structural information about a loaded DataFrame."""

    def inspect(
        self,
        dataframe: pd.DataFrame | None,
    ) -> DataInspectionResult:
        """Inspect shape, columns, data types, and missing values."""

        if dataframe is None:
            return DataInspectionResult(
                success=False,
                row_count=0,
                column_count=0,
                column_names=[],
                dtypes={},
                missing_value_counts={},
                error="No dataframe provided to inspect.",
            )

        row_count, column_count = dataframe.shape

        column_names = [
            str(column)
            for column in dataframe.columns
        ]

        dtypes = {
            str(column): str(dtype)
            for column, dtype in dataframe.dtypes.items()
        }

        missing_value_counts = {
            str(column): int(count)
            for column, count in dataframe.isna().sum().items()
        }

        return DataInspectionResult(
            success=True,
            row_count=row_count,
            column_count=column_count,
            column_names=column_names,
            dtypes=dtypes,
            missing_value_counts=missing_value_counts,
        )


class DataAnalyzer:
    """
    Performs business-oriented deterministic analysis.

    For sales datasets, Nexora analyzes:

    - Sales
    - Profit
    - Discount
    - Quantity

    It calculates descriptive statistics and uses the IQR rule
    to identify unusual values.

    This is statistical analysis, NOT ML-based anomaly detection.
    """

    def analyze(
        self,
        dataframe: pd.DataFrame | None,
    ) -> DataAnalysisResult:
        """Analyze a sales-oriented DataFrame."""

        if dataframe is None:
            return DataAnalysisResult(
                success=False,
                numeric_columns=[],
                statistics=[],
                unusual_values=[],
                error="No dataframe provided to analyze.",
            )

        # Only analyze meaningful business metrics.
        available_columns = [
            column
            for column in dataframe.columns
            if str(column) in _BUSINESS_NUMERIC_COLUMNS
        ]

        if not available_columns:
            return DataAnalysisResult(
                success=True,
                numeric_columns=[],
                statistics=[],
                unusual_values=[],
                error="No supported business numeric columns found.",
            )

        statistics: list[ColumnStatistics] = []
        unusual_values: list[UnusualValue] = []

        for column in available_columns:
            column_name = str(column)

            series = pd.to_numeric(
                dataframe[column],
                errors="coerce",
            ).dropna()

            if series.empty:
                continue

            statistics.append(
                ColumnStatistics(
                    column=column_name,
                    count=int(series.count()),
                    mean=float(series.mean()),
                    std=(
                        float(series.std())
                        if series.count() > 1
                        else 0.0
                    ),
                    min=float(series.min()),
                    max=float(series.max()),
                    median=float(series.median()),
                )
            )

            unusual_values.extend(
                self._find_unusual_values(
                    column_name,
                    series,
                )
            )

        # -------------------------
        # Sales analysis
        # -------------------------

        total_sales = 0.0
        average_sales = 0.0

        if "Sales" in dataframe.columns:
            sales = pd.to_numeric(
                dataframe["Sales"],
                errors="coerce",
            ).dropna()

            if not sales.empty:
                total_sales = float(sales.sum())
                average_sales = float(sales.mean())

        # -------------------------
        # Profit analysis
        # -------------------------

        total_profit = 0.0
        average_profit = 0.0
        loss_making_transactions = 0

        if "Profit" in dataframe.columns:
            profit = pd.to_numeric(
                dataframe["Profit"],
                errors="coerce",
            ).dropna()

            if not profit.empty:
                total_profit = float(profit.sum())
                average_profit = float(profit.mean())
                loss_making_transactions = int(
                    (profit < 0).sum()
                )

        # -------------------------
        # Quantity analysis
        # -------------------------

        total_quantity = 0
        average_quantity = 0.0

        if "Quantity" in dataframe.columns:
            quantity = pd.to_numeric(
                dataframe["Quantity"],
                errors="coerce",
            ).dropna()

            if not quantity.empty:
                total_quantity = int(quantity.sum())
                average_quantity = float(quantity.mean())

        # -------------------------
        # Discount analysis
        # -------------------------

        average_discount = 0.0
        high_discount_transactions = 0

        if "Discount" in dataframe.columns:
            discount = pd.to_numeric(
                dataframe["Discount"],
                errors="coerce",
            ).dropna()

            if not discount.empty:
                average_discount = float(discount.mean())

                # Treat discounts >= 50% as high discounts.
                high_discount_transactions = int(
                    (discount >= 0.50).sum()
                )

        return DataAnalysisResult(
            success=True,
            numeric_columns=[
                str(column)
                for column in available_columns
            ],
            statistics=statistics,
            unusual_values=unusual_values,
            total_sales=total_sales,
            average_sales=average_sales,
            total_profit=total_profit,
            average_profit=average_profit,
            total_quantity=total_quantity,
            average_quantity=average_quantity,
            average_discount=average_discount,
            loss_making_transactions=loss_making_transactions,
            high_discount_transactions=high_discount_transactions,
        )

    @staticmethod
    def _find_unusual_values(
        column: str,
        series: pd.Series,
    ) -> list[UnusualValue]:
        """Find values outside the standard IQR bounds."""

        if series.count() < 4:
            return []

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        if iqr == 0:
            return []

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = series[
            (series < lower_bound)
            | (series > upper_bound)
        ]

        return [
            UnusualValue(
                column=column,
                row_index=int(index),
                value=float(value),
            )
            for index, value in outliers.items()
        ]