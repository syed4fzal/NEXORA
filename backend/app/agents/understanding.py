"""
app/agents/understanding.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Local, deterministic Task Understanding component for Nexora.

Phase 6 improvements:
- Better recognition of data-analysis requests.
- Supports business-analysis terminology.
- Recognizes sales, profit, revenue, discount, product, category,
  region, performance, transactions, losses, and unusual values.
- Supports both "analyze" and "analyse".
- Keeps existing document and general-task behavior compatible.
- No LLM, external API, network access, or ML models are used.
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------
# Common stopwords
# ---------------------------------------------------------------------

_STOPWORDS: frozenset[str] = frozenset(
    {
        "this",
        "the",
        "a",
        "an",
        "that",
        "these",
        "those",
        "my",
        "our",
        "your",
        "this",
        "its",
    }
)


# ---------------------------------------------------------------------
# Data-analysis nouns
# ---------------------------------------------------------------------

_DATA_ANALYSIS_NOUNS: frozenset[str] = frozenset(
    {
        # Files / datasets
        "csv",
        "data",
        "dataset",
        "spreadsheet",
        "excel",
        "sheet",

        # Transactions
        "transaction",
        "transactions",

        # Business metrics
        "sales",
        "sale",
        "profit",
        "profits",
        "revenue",
        "discount",
        "discounts",

        # Business dimensions
        "product",
        "products",
        "category",
        "categories",
        "region",
        "regions",
        "regional",

        # Performance
        "performance",
        "loss",
        "losses",
        "loss-making",

        # Statistical analysis
        "statistics",
        "statistical",
        "outlier",
        "outliers",
        "unusual",
        "anomaly",
        "anomalies",
    }
)


# ---------------------------------------------------------------------
# Data-analysis actions
# ---------------------------------------------------------------------

_DATA_ANALYSIS_ACTIONS: dict[str, str] = {
    "analyze": "analyze",
    "analyse": "analyze",
    "find": "find",
    "review": "review",
    "inspect": "inspect",
    "examine": "analyze",
    "evaluate": "analyze",
    "check": "analyze",
    "identify": "find",
    "detect": "find",
}


# ---------------------------------------------------------------------
# Document nouns
# ---------------------------------------------------------------------

_DOCUMENT_NOUNS: frozenset[str] = frozenset(
    {
        "document",
        "doc",
        "pdf",
        "report",
        "file",
        "text",
        "article",
    }
)


# ---------------------------------------------------------------------
# Document actions
# ---------------------------------------------------------------------

_DOCUMENT_ACTIONS: dict[str, str] = {
    "summarize": "summarize",
    "summarise": "summarize",
    "review": "review",
    "read": "read",
    "extract": "extract",
}


# ---------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------

@dataclass
class TaskUnderstandingResult:
    """Structured understanding of a natural-language task description."""

    intent: str
    action: str
    target: str
    requires_data: bool


# ---------------------------------------------------------------------
# Task Understanding
# ---------------------------------------------------------------------

class TaskUnderstanding:
    """Deterministic rule-based task classifier for Nexora.

    The classifier identifies:
    - data-analysis tasks
    - document tasks
    - general tasks

    No LLM, external API, network access, or ML model is used.
    """

    def understand(self, task: str) -> TaskUnderstandingResult:
        """Analyze a natural-language task description.

        Args:
            task:
                Raw task description.

        Returns:
            TaskUnderstandingResult containing:
            - intent
            - action
            - target
            - requires_data
        """

        cleaned_task = task.strip()

        if not cleaned_task:
            return TaskUnderstandingResult(
                intent="general",
                action="process",
                target="",
                requires_data=False,
            )

        tokens = cleaned_task.split()

        lowered_tokens = [
            token.lower().strip(".,!?:;()[]{}")
            for token in tokens
        ]

        # -------------------------------------------------------------
        # Data analysis
        # -------------------------------------------------------------

        if self._is_data_analysis_task(lowered_tokens):
            action = self._find_action(
                lowered_tokens,
                _DATA_ANALYSIS_ACTIONS,
                default="analyze",
            )

            target = self._extract_data_target(
                tokens,
                lowered_tokens,
            )

            return TaskUnderstandingResult(
                intent="data_analysis",
                action=action,
                target=target,
                requires_data=True,
            )

        # -------------------------------------------------------------
        # Document
        # -------------------------------------------------------------

        if self._contains_any(
            lowered_tokens,
            _DOCUMENT_NOUNS,
        ):
            action = self._find_action(
                lowered_tokens,
                _DOCUMENT_ACTIONS,
                default="summarize",
            )

            target = self._extract_target(
                tokens,
                lowered_tokens,
                _DOCUMENT_NOUNS,
            )

            return TaskUnderstandingResult(
                intent="document",
                action=action,
                target=target,
                requires_data=True,
            )

        # -------------------------------------------------------------
        # General
        # -------------------------------------------------------------

        return TaskUnderstandingResult(
            intent="general",
            action="process",
            target=cleaned_task,
            requires_data=False,
        )

    # -----------------------------------------------------------------
    # Data-analysis detection
    # -----------------------------------------------------------------

    @staticmethod
    def _is_data_analysis_task(
        lowered_tokens: list[str],
    ) -> bool:
        """Determine whether a request is a data-analysis task."""

        # Explicit dataset/file indicators
        if TaskUnderstanding._contains_any(
            lowered_tokens,
            _DATA_ANALYSIS_NOUNS,
        ):
            return True

        return False

    # -----------------------------------------------------------------
    # Generic keyword check
    # -----------------------------------------------------------------

    @staticmethod
    def _contains_any(
        lowered_tokens: list[str],
        keywords: frozenset[str],
    ) -> bool:
        """Return True when any token matches a keyword."""

        return any(
            token in keywords
            for token in lowered_tokens
        )

    # -----------------------------------------------------------------
    # Action detection
    # -----------------------------------------------------------------

    @staticmethod
    def _find_action(
        lowered_tokens: list[str],
        action_keywords: dict[str, str],
        default: str,
    ) -> str:
        """Return the first recognized action."""

        for token in lowered_tokens:
            if token in action_keywords:
                return action_keywords[token]

        return default

    # -----------------------------------------------------------------
    # Data target extraction
    # -----------------------------------------------------------------

    @staticmethod
    def _extract_data_target(
        tokens: list[str],
        lowered_tokens: list[str],
    ) -> str:
        """Extract a useful target phrase from a data-analysis request.

        Examples:

            "Analyze the sales performance"
                -> "sales performance"

            "Analyze profit"
                -> "profit"

            "Find loss-making transactions"
                -> "loss-making transactions"

            "Analyze sales by region"
                -> "sales by region"
        """

        # -------------------------------------------------------------
        # Find the first meaningful data/business keyword.
        # -------------------------------------------------------------

        first_index: int | None = None

        for index, token in enumerate(lowered_tokens):
            if token in _DATA_ANALYSIS_NOUNS:
                first_index = index
                break

        if first_index is None:
            return " ".join(tokens)

        # -------------------------------------------------------------
        # Build target from the first meaningful keyword.
        # -------------------------------------------------------------

        target_tokens: list[str] = []

        for index in range(
            first_index,
            len(tokens),
        ):
            current_lower = lowered_tokens[index]

            # Stop at common command separators.
            if current_lower in {
                "and",
                "then",
                "please",
            } and target_tokens:
                break

            target_tokens.append(
                tokens[index].strip(".,!?:;()[]{}")
            )

        target = " ".join(target_tokens).strip()

        if target:
            return target

        return tokens[first_index].strip(
            ".,!?:;()[]{}"
        )

    # -----------------------------------------------------------------
    # Generic target extraction
    # -----------------------------------------------------------------

    @staticmethod
    def _extract_target(
        tokens: list[str],
        lowered_tokens: list[str],
        noun_keywords: frozenset[str],
    ) -> str:
        """Build a short target phrase around a recognized noun."""

        for index, token in enumerate(lowered_tokens):

            if token not in noun_keywords:
                continue

            noun = tokens[index].strip(
                ".,!?:;()[]{}"
            )

            # Include the previous word if it is useful.
            if index > 0:

                previous_word = tokens[index - 1].strip(
                    ".,!?:;()[]{}"
                )

                if (
                    previous_word.lower()
                    not in _STOPWORDS
                ):
                    return f"{previous_word} {noun}"

            return noun

        return " ".join(tokens)