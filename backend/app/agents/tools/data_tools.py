"""
app/agents/tools/data_tools.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Local, deterministic data-handling and business-analysis tools for Nexora.

Supports:
- CSV loading
- Excel loading
- Dataset inspection
- Basic statistical analysis
- IQR-based unusual-value detection
- Sales analysis
- Profit and loss analysis
- Discount analysis
- Category analysis
- Region analysis
- Product analysis
- Loss-making transaction analysis
- Combined business analysis

No network access, no LLM, no external API, and no ML models are used.
Everything is performed locally using pandas and deterministic statistics.

IMPORTANT:
IQR unusual-value detection is only a basic statistical outlier check.
It is NOT anomaly detection, fraud detection, or ML-based analysis.
"""

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


_SUPPORTED_CSV_EXTENSIONS = {".csv"}
_SUPPORTED_EXCEL_EXTENSIONS = {".xlsx", ".xls"}


def _validate_columns(
    dataframe: pd.DataFrame,
    required_columns: list[str],
) -> list[str]:
    """Return the required columns that are missing."""
    return [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]


# ---------------------------------------------------------------------
# Result data classes
# ---------------------------------------------------------------------


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
    """Basic descriptive statistics for a numeric column."""

    column: str
    count: int
    mean: float
    std: float
    min: float
    max: float
    median: float


@dataclass
class UnusualValue:
    """A value flagged by the IQR outlier check."""

    column: str
    row_index: int
    value: float


@dataclass
class DataAnalysisResult:
    """Basic deterministic statistical analysis result."""

    success: bool
    numeric_columns: list[str]
    statistics: list[ColumnStatistics]
    unusual_values: list[UnusualValue]
    error: str | None = None


@dataclass
class SalesAnalysisResult:
    """Sales and quantity analysis result."""

    success: bool
    total_sales: float = 0.0
    average_sales: float = 0.0
    median_sales: float = 0.0
    minimum_sales: float = 0.0
    maximum_sales: float = 0.0
    total_quantity: float = 0.0
    error: str | None = None


@dataclass
class ProfitAnalysisResult:
    """Profit and loss analysis result."""

    success: bool
    total_profit: float = 0.0
    average_profit: float = 0.0
    median_profit: float = 0.0
    minimum_profit: float = 0.0
    maximum_profit: float = 0.0
    loss_making_transactions: int = 0
    profitable_transactions: int = 0
    profit_margin_percentage: float = 0.0
    error: str | None = None


@dataclass
class DiscountAnalysisResult:
    """Discount analysis result."""

    success: bool
    average_discount: float = 0.0
    minimum_discount: float = 0.0
    maximum_discount: float = 0.0
    high_discount_transactions: int = 0
    very_high_discount_transactions: int = 0
    error: str | None = None


@dataclass
class CategoryAnalysisResult:
    """Sales and profit breakdown by category."""

    success: bool
    highest_sales_category: str | None = None
    lowest_sales_category: str | None = None
    highest_profit_category: str | None = None
    lowest_profit_category: str | None = None
    sales_by_category: dict[str, float] = field(default_factory=dict)
    profit_by_category: dict[str, float] = field(default_factory=dict)
    error: str | None = None


@dataclass
class RegionAnalysisResult:
    """Sales and profit breakdown by region."""

    success: bool
    highest_sales_region: str | None = None
    lowest_sales_region: str | None = None
    highest_profit_region: str | None = None
    lowest_profit_region: str | None = None
    sales_by_region: dict[str, float] = field(default_factory=dict)
    profit_by_region: dict[str, float] = field(default_factory=dict)
    error: str | None = None


@dataclass
class ProductAnalysisResult:
    """Sales and profit breakdown by product."""

    success: bool
    highest_sales_product: str | None = None
    highest_profit_product: str | None = None
    lowest_profit_product: str | None = None
    top_10_products_by_sales: dict[str, float] = field(
        default_factory=dict
    )
    top_10_products_by_profit: dict[str, float] = field(
        default_factory=dict
    )
    bottom_10_products_by_profit: dict[str, float] = field(
        default_factory=dict
    )
    error: str | None = None


@dataclass
class LossAnalysisResult:
    """Analysis of loss-making transactions."""

    success: bool
    loss_making_transactions: int = 0
    total_loss: float = 0.0
    average_loss: float = 0.0
    maximum_loss: float = 0.0
    top_loss_making_transactions: list[dict[str, object]] = field(
        default_factory=list
    )
    error: str | None = None


@dataclass
class UnusualValueSummary:
    """Summary of IQR-flagged unusual numeric values."""

    success: bool
    total_unusual_values: int = 0
    unusual_values_by_column: dict[str, int] = field(
        default_factory=dict
    )
    numeric_columns: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class BusinessAnalysisResult:
    """Combined deterministic business analysis result."""

    success: bool
    basic_analysis: DataAnalysisResult | None = None
    sales_analysis: SalesAnalysisResult | None = None
    profit_analysis: ProfitAnalysisResult | None = None
    discount_analysis: DiscountAnalysisResult | None = None
    category_analysis: CategoryAnalysisResult | None = None
    region_analysis: RegionAnalysisResult | None = None
    product_analysis: ProductAnalysisResult | None = None
    loss_analysis: LossAnalysisResult | None = None
    unusual_value_summary: UnusualValueSummary | None = None
    error: str | None = None


# ---------------------------------------------------------------------
# Data Loader
# ---------------------------------------------------------------------


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
                    engine="openpyxl"
                    if extension == ".xlsx"
                    else None,
                )

            else:
                return DataLoadResult(
                    success=False,
                    file_path=file_path,
                    rows=0,
                    columns=0,
                    error=(
                        "Unsupported file extension: "
                        f"{extension or '(none)'}"
                    ),
                )

        except Exception as exc:
            return DataLoadResult(
                success=False,
                file_path=file_path,
                rows=0,
                columns=0,
                error=(
                    "Failed to read file: "
                    f"{exc.__class__.__name__}"
                ),
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
        """Load CSV using UTF-8 and Latin-1 fallback."""

        try:
            return pd.read_csv(
                path,
                encoding="utf-8",
            )
        except UnicodeDecodeError:
            return pd.read_csv(
                path,
                encoding="latin1",
            )


# ---------------------------------------------------------------------
# Data Inspector
# ---------------------------------------------------------------------


class DataInspector:
    """Reports structural information about a DataFrame."""

    def inspect(
        self,
        dataframe: pd.DataFrame | None,
    ) -> DataInspectionResult:
        """Inspect shape, columns, types, and missing values."""

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


# ---------------------------------------------------------------------
# Data Analyzer
# ---------------------------------------------------------------------


class DataAnalyzer:
    """
    Performs deterministic statistical and business analysis.

    No LLM, network access, external API, or ML model is used.
    """

    # -------------------------------------------------------------
    # Basic statistical analysis
    # -------------------------------------------------------------

    def analyze(
        self,
        dataframe: pd.DataFrame | None,
    ) -> DataAnalysisResult:
        """Analyze numeric columns using descriptive statistics and IQR."""

        if dataframe is None:
            return DataAnalysisResult(
                success=False,
                numeric_columns=[],
                statistics=[],
                unusual_values=[],
                error="No dataframe provided to analyze.",
            )

        numeric_dataframe = dataframe.select_dtypes(
            include="number"
        )

        numeric_columns = [
            str(column)
            for column in numeric_dataframe.columns
        ]

        if not numeric_columns:
            return DataAnalysisResult(
                success=True,
                numeric_columns=[],
                statistics=[],
                unusual_values=[],
            )

        statistics: list[ColumnStatistics] = []
        unusual_values: list[UnusualValue] = []

        for column in numeric_dataframe.columns:
            series = numeric_dataframe[column].dropna()

            if series.empty:
                continue

            statistics.append(
                ColumnStatistics(
                    column=str(column),
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
                    str(column),
                    series,
                )
            )

        return DataAnalysisResult(
            success=True,
            numeric_columns=numeric_columns,
            statistics=statistics,
            unusual_values=unusual_values,
        )

    @staticmethod
    def _find_unusual_values(
        column: str,
        series: pd.Series,
    ) -> list[UnusualValue]:
        """Find values outside standard IQR bounds."""

        if series.count() < 4:
            return []

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        if iqr == 0:
            return []

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

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

    # -------------------------------------------------------------
    # Sales analysis
    # -------------------------------------------------------------

    def analyze_sales(
        self,
        dataframe: pd.DataFrame | None,
    ) -> SalesAnalysisResult:
        """Analyze sales and quantity."""

        if dataframe is None:
            return SalesAnalysisResult(
                success=False,
                error="No dataframe provided.",
            )

        missing = _validate_columns(
            dataframe,
            ["Sales", "Quantity"],
        )

        if missing:
            return SalesAnalysisResult(
                success=False,
                error=(
                    "Missing required columns: "
                    + ", ".join(missing)
                ),
            )

        sales = pd.to_numeric(
            dataframe["Sales"],
            errors="coerce",
        ).dropna()

        quantity = pd.to_numeric(
            dataframe["Quantity"],
            errors="coerce",
        ).dropna()

        if sales.empty:
            return SalesAnalysisResult(
                success=False,
                error="Sales column contains no valid numeric values.",
            )

        return SalesAnalysisResult(
            success=True,
            total_sales=float(sales.sum()),
            average_sales=float(sales.mean()),
            median_sales=float(sales.median()),
            minimum_sales=float(sales.min()),
            maximum_sales=float(sales.max()),
            total_quantity=float(quantity.sum()),
        )

    # -------------------------------------------------------------
    # Profit analysis
    # -------------------------------------------------------------

    def analyze_profit(
        self,
        dataframe: pd.DataFrame | None,
    ) -> ProfitAnalysisResult:
        """Analyze profit, losses, and profit margin."""

        if dataframe is None:
            return ProfitAnalysisResult(
                success=False,
                error="No dataframe provided.",
            )

        missing = _validate_columns(
            dataframe,
            ["Profit", "Sales"],
        )

        if missing:
            return ProfitAnalysisResult(
                success=False,
                error=(
                    "Missing required columns: "
                    + ", ".join(missing)
                ),
            )

        profit = pd.to_numeric(
            dataframe["Profit"],
            errors="coerce",
        ).dropna()

        sales = pd.to_numeric(
            dataframe["Sales"],
            errors="coerce",
        ).dropna()

        if profit.empty:
            return ProfitAnalysisResult(
                success=False,
                error="Profit column contains no valid numeric values.",
            )

        total_profit = float(profit.sum())
        total_sales = float(sales.sum())

        margin = (
            (total_profit / total_sales) * 100
            if total_sales != 0
            else 0.0
        )

        return ProfitAnalysisResult(
            success=True,
            total_profit=total_profit,
            average_profit=float(profit.mean()),
            median_profit=float(profit.median()),
            minimum_profit=float(profit.min()),
            maximum_profit=float(profit.max()),
            loss_making_transactions=int(
                (profit < 0).sum()
            ),
            profitable_transactions=int(
                (profit > 0).sum()
            ),
            profit_margin_percentage=float(margin),
        )

    # -------------------------------------------------------------
    # Discount analysis
    # -------------------------------------------------------------

    def analyze_discounts(
        self,
        dataframe: pd.DataFrame | None,
    ) -> DiscountAnalysisResult:
        """Analyze discount levels."""

        if dataframe is None:
            return DiscountAnalysisResult(
                success=False,
                error="No dataframe provided.",
            )

        missing = _validate_columns(
            dataframe,
            ["Discount"],
        )

        if missing:
            return DiscountAnalysisResult(
                success=False,
                error="Missing required columns: Discount",
            )

        discount = pd.to_numeric(
            dataframe["Discount"],
            errors="coerce",
        ).dropna()

        if discount.empty:
            return DiscountAnalysisResult(
                success=False,
                error=(
                    "Discount column contains no valid "
                    "numeric values."
                ),
            )

        return DiscountAnalysisResult(
            success=True,
            average_discount=float(discount.mean()),
            minimum_discount=float(discount.min()),
            maximum_discount=float(discount.max()),
            high_discount_transactions=int(
                (discount > 0.5).sum()
            ),
            very_high_discount_transactions=int(
                (discount > 0.7).sum()
            ),
        )

    # -------------------------------------------------------------
    # Category analysis
    # -------------------------------------------------------------

    def analyze_categories(
        self,
        dataframe: pd.DataFrame | None,
    ) -> CategoryAnalysisResult:
        """Analyze sales and profit by category."""

        if dataframe is None:
            return CategoryAnalysisResult(
                success=False,
                error="No dataframe provided.",
            )

        missing = _validate_columns(
            dataframe,
            ["Category", "Sales", "Profit"],
        )

        if missing:
            return CategoryAnalysisResult(
                success=False,
                error=(
                    "Missing required columns: "
                    + ", ".join(missing)
                ),
            )

        grouped = dataframe.copy()

        grouped["Sales"] = pd.to_numeric(
            grouped["Sales"],
            errors="coerce",
        )

        grouped["Profit"] = pd.to_numeric(
            grouped["Profit"],
            errors="coerce",
        )

        grouped = grouped.dropna(
            subset=["Category", "Sales", "Profit"]
        )

        sales_by_category = (
            grouped.groupby("Category")["Sales"]
            .sum()
            .sort_values(ascending=False)
        )

        profit_by_category = (
            grouped.groupby("Category")["Profit"]
            .sum()
            .sort_values(ascending=False)
        )

        if sales_by_category.empty:
            return CategoryAnalysisResult(
                success=False,
                error="No valid category data found.",
            )

        return CategoryAnalysisResult(
            success=True,
            highest_sales_category=str(
                sales_by_category.idxmax()
            ),
            lowest_sales_category=str(
                sales_by_category.idxmin()
            ),
            highest_profit_category=str(
                profit_by_category.idxmax()
            ),
            lowest_profit_category=str(
                profit_by_category.idxmin()
            ),
            sales_by_category={
                str(key): float(value)
                for key, value in sales_by_category.items()
            },
            profit_by_category={
                str(key): float(value)
                for key, value in profit_by_category.items()
            },
        )

    # -------------------------------------------------------------
    # Region analysis
    # -------------------------------------------------------------

    def analyze_regions(
        self,
        dataframe: pd.DataFrame | None,
    ) -> RegionAnalysisResult:
        """Analyze sales and profit by region."""

        if dataframe is None:
            return RegionAnalysisResult(
                success=False,
                error="No dataframe provided.",
            )

        missing = _validate_columns(
            dataframe,
            ["Region", "Sales", "Profit"],
        )

        if missing:
            return RegionAnalysisResult(
                success=False,
                error=(
                    "Missing required columns: "
                    + ", ".join(missing)
                ),
            )

        grouped = dataframe.copy()

        grouped["Sales"] = pd.to_numeric(
            grouped["Sales"],
            errors="coerce",
        )

        grouped["Profit"] = pd.to_numeric(
            grouped["Profit"],
            errors="coerce",
        )

        grouped = grouped.dropna(
            subset=["Region", "Sales", "Profit"]
        )

        sales_by_region = (
            grouped.groupby("Region")["Sales"]
            .sum()
            .sort_values(ascending=False)
        )

        profit_by_region = (
            grouped.groupby("Region")["Profit"]
            .sum()
            .sort_values(ascending=False)
        )

        if sales_by_region.empty:
            return RegionAnalysisResult(
                success=False,
                error="No valid region data found.",
            )

        return RegionAnalysisResult(
            success=True,
            highest_sales_region=str(
                sales_by_region.idxmax()
            ),
            lowest_sales_region=str(
                sales_by_region.idxmin()
            ),
            highest_profit_region=str(
                profit_by_region.idxmax()
            ),
            lowest_profit_region=str(
                profit_by_region.idxmin()
            ),
            sales_by_region={
                str(key): float(value)
                for key, value in sales_by_region.items()
            },
            profit_by_region={
                str(key): float(value)
                for key, value in profit_by_region.items()
            },
        )

    # -------------------------------------------------------------
    # Product analysis
    # -------------------------------------------------------------

    def analyze_products(
        self,
        dataframe: pd.DataFrame | None,
    ) -> ProductAnalysisResult:
        """Analyze sales and profit by product."""

        if dataframe is None:
            return ProductAnalysisResult(
                success=False,
                error="No dataframe provided.",
            )

        missing = _validate_columns(
            dataframe,
            ["Product Name", "Sales", "Profit"],
        )

        if missing:
            return ProductAnalysisResult(
                success=False,
                error=(
                    "Missing required columns: "
                    + ", ".join(missing)
                ),
            )

        grouped = dataframe.copy()

        grouped["Sales"] = pd.to_numeric(
            grouped["Sales"],
            errors="coerce",
        )

        grouped["Profit"] = pd.to_numeric(
            grouped["Profit"],
            errors="coerce",
        )

        grouped = grouped.dropna(
            subset=["Product Name", "Sales", "Profit"]
        )

        sales_by_product = (
            grouped.groupby("Product Name")["Sales"]
            .sum()
            .sort_values(ascending=False)
        )

        profit_by_product = (
            grouped.groupby("Product Name")["Profit"]
            .sum()
            .sort_values(ascending=False)
        )

        if sales_by_product.empty:
            return ProductAnalysisResult(
                success=False,
                error="No valid product data found.",
            )

        return ProductAnalysisResult(
            success=True,
            highest_sales_product=str(
                sales_by_product.idxmax()
            ),
            highest_profit_product=str(
                profit_by_product.idxmax()
            ),
            lowest_profit_product=str(
                profit_by_product.idxmin()
            ),
            top_10_products_by_sales={
                str(key): float(value)
                for key, value in sales_by_product.head(10).items()
            },
            top_10_products_by_profit={
                str(key): float(value)
                for key, value in profit_by_product.head(10).items()
            },
            bottom_10_products_by_profit={
                str(key): float(value)
                for key, value in profit_by_product.tail(10).items()
            },
        )

    # -------------------------------------------------------------
    # Loss analysis
    # -------------------------------------------------------------

    def find_loss_making_transactions(
        self,
        dataframe: pd.DataFrame | None,
    ) -> LossAnalysisResult:
        """Find and summarize transactions with negative profit."""

        if dataframe is None:
            return LossAnalysisResult(
                success=False,
                error="No dataframe provided.",
            )

        missing = _validate_columns(
            dataframe,
            ["Profit"],
        )

        if missing:
            return LossAnalysisResult(
                success=False,
                error="Missing required columns: Profit",
            )

        working = dataframe.copy()

        working["Profit"] = pd.to_numeric(
            working["Profit"],
            errors="coerce",
        )

        losses = working[
            working["Profit"] < 0
        ].copy()

        if losses.empty:
            return LossAnalysisResult(
                success=True,
            )

        total_loss = float(
            losses["Profit"].sum()
        )

        average_loss = float(
            losses["Profit"].mean()
        )

        maximum_loss = float(
            losses["Profit"].min()
        )

        preferred_columns = [
            "Order ID",
            "Product Name",
            "Category",
            "Sub-Category",
            "Sales",
            "Profit",
        ]

        available_columns = [
            column
            for column in preferred_columns
            if column in losses.columns
        ]

        top_losses = (
            losses.sort_values(
                by="Profit",
                ascending=True,
            )
            .head(10)
        )

        records: list[dict[str, object]] = []

        for _, row in top_losses.iterrows():
            record: dict[str, object] = {}

            for column in available_columns:
                value = row[column]

                if pd.isna(value):
                    record[column] = None
                elif isinstance(value, (int, float)):
                    record[column] = float(value)
                else:
                    record[column] = str(value)

            records.append(record)

        return LossAnalysisResult(
            success=True,
            loss_making_transactions=int(len(losses)),
            total_loss=total_loss,
            average_loss=average_loss,
            maximum_loss=maximum_loss,
            top_loss_making_transactions=records,
        )

    # -------------------------------------------------------------
    # Unusual value summary
    # -------------------------------------------------------------

    def summarize_unusual_values(
        self,
        dataframe: pd.DataFrame | None,
    ) -> UnusualValueSummary:
        """Summarize IQR-flagged unusual numeric values."""

        if dataframe is None:
            return UnusualValueSummary(
                success=False,
                error="No dataframe provided.",
            )

        result = self.analyze(dataframe)

        if not result.success:
            return UnusualValueSummary(
                success=False,
                error=result.error,
            )

        by_column: dict[str, int] = {}

        for unusual in result.unusual_values:
            by_column[unusual.column] = (
                by_column.get(unusual.column, 0) + 1
            )

        return UnusualValueSummary(
            success=True,
            total_unusual_values=len(
                result.unusual_values
            ),
            unusual_values_by_column=by_column,
            numeric_columns=result.numeric_columns,
        )

    # -------------------------------------------------------------
    # Complete business analysis
    # -------------------------------------------------------------

    def analyze_business_data(
        self,
        dataframe: pd.DataFrame | None,
    ) -> BusinessAnalysisResult:
        """Run the complete deterministic business-analysis pipeline."""

        if dataframe is None:
            return BusinessAnalysisResult(
                success=False,
                error="No dataframe provided.",
            )

        basic = self.analyze(dataframe)
        sales = self.analyze_sales(dataframe)
        profit = self.analyze_profit(dataframe)
        discount = self.analyze_discounts(dataframe)
        category = self.analyze_categories(dataframe)
        region = self.analyze_regions(dataframe)
        product = self.analyze_products(dataframe)
        loss = self.find_loss_making_transactions(dataframe)
        unusual = self.summarize_unusual_values(dataframe)

        analyses = [
            basic,
            sales,
            profit,
            discount,
            category,
            region,
            product,
            loss,
            unusual,
        ]

        successful = all(
            getattr(result, "success", False)
            for result in analyses
        )

        errors = [
            getattr(result, "error", None)
            for result in analyses
            if not getattr(result, "success", False)
        ]

        return BusinessAnalysisResult(
            success=successful,
            basic_analysis=basic,
            sales_analysis=sales,
            profit_analysis=profit,
            discount_analysis=discount,
            category_analysis=category,
            region_analysis=region,
            product_analysis=product,
            loss_analysis=loss,
            unusual_value_summary=unusual,
            error="; ".join(
                error
                for error in errors
                if error
            ) or None,
        )