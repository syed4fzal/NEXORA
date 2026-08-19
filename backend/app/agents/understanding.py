"""
app/agents/understanding.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Local, deterministic Task Understanding component for Nexora.

This is intentionally simple, rule-based logic -- no LLM, no external
calls. It is the first version of "task understanding" and is expected
to be replaced or enhanced by a real reasoning system in a later phase.
"""

from dataclasses import dataclass

# Words that should not be treated as part of a target phrase when they
# appear immediately before a recognized target noun (e.g. "this document").
_STOPWORDS: frozenset[str] = frozenset(
    {"this", "the", "a", "an", "that", "these", "those", "my", "our", "your"}
)

# Nouns that indicate a "data_analysis" task, and the actions we look for.
_DATA_ANALYSIS_NOUNS: frozenset[str] = frozenset(
    {"csv", "data", "dataset", "spreadsheet", "excel", "transactions", "transaction", "sheet"}
)
_DATA_ANALYSIS_ACTIONS: dict[str, str] = {
    "analyze": "analyze",
    "analyse": "analyze",
    "find": "find",
    "review": "review",
    "inspect": "inspect",
}

# Nouns that indicate a "document" task, and the actions we look for.
_DOCUMENT_NOUNS: frozenset[str] = frozenset(
    {"document", "doc", "pdf", "report", "file", "text", "article"}
)
_DOCUMENT_ACTIONS: dict[str, str] = {
    "summarize": "summarize",
    "summarise": "summarize",
    "review": "review",
    "read": "read",
    "extract": "extract",
}


@dataclass
class TaskUnderstandingResult:
    """Structured understanding of a natural-language task description."""

    intent: str
    action: str
    target: str
    requires_data: bool


class TaskUnderstanding:
    """A small, deterministic rule-based task classifier.

    This is a placeholder for a future, more capable reasoning system.
    It recognizes a few basic task categories using simple keyword
    matching -- no LLM or external API is involved.
    """

    def understand(self, task: str) -> TaskUnderstandingResult:
        """Analyze a natural-language task description.

        Args:
            task: The raw task description, e.g.
                "Analyze this sales CSV and find unusual transactions".

        Returns:
            A TaskUnderstandingResult with `intent`, `action`, `target`,
            and `requires_data` populated using simple keyword rules.
        """
        cleaned_task = task.strip()
        tokens = cleaned_task.split()
        lowered_tokens = [token.lower().strip(".,!?:;") for token in tokens]

        if self._contains_any(lowered_tokens, _DATA_ANALYSIS_NOUNS):
            action = self._find_action(lowered_tokens, _DATA_ANALYSIS_ACTIONS, default="analyze")
            target = self._extract_target(tokens, lowered_tokens, _DATA_ANALYSIS_NOUNS)
            return TaskUnderstandingResult(
                intent="data_analysis",
                action=action,
                target=target,
                requires_data=True,
            )

        if self._contains_any(lowered_tokens, _DOCUMENT_NOUNS):
            action = self._find_action(lowered_tokens, _DOCUMENT_ACTIONS, default="summarize")
            target = self._extract_target(tokens, lowered_tokens, _DOCUMENT_NOUNS)
            return TaskUnderstandingResult(
                intent="document",
                action=action,
                target=target,
                requires_data=True,
            )

        return TaskUnderstandingResult(
            intent="general",
            action="process",
            target=cleaned_task,
            requires_data=False,
        )

    @staticmethod
    def _contains_any(lowered_tokens: list[str], keywords: frozenset[str]) -> bool:
        """Return True if any token matches one of the given keywords."""
        return any(token in keywords for token in lowered_tokens)

    @staticmethod
    def _find_action(
        lowered_tokens: list[str], action_keywords: dict[str, str], default: str
    ) -> str:
        """Return the first recognized action keyword found, or a default."""
        for token in lowered_tokens:
            if token in action_keywords:
                return action_keywords[token]
        return default

    @staticmethod
    def _extract_target(
        tokens: list[str], lowered_tokens: list[str], noun_keywords: frozenset[str]
    ) -> str:
        """Build a short target phrase around the first recognized noun.

        Includes the preceding word as a qualifier (e.g. "sales" + "CSV"
        -> "sales CSV") unless that word is a stopword like "this"/"the".
        """
        for index, token in enumerate(lowered_tokens):
            if token in noun_keywords:
                noun = tokens[index].strip(".,!?:;")
                if index > 0:
                    previous_word = tokens[index - 1].strip(".,!?:;")
                    if previous_word.lower() not in _STOPWORDS:
                        return f"{previous_word} {noun}"
                return noun
        return " ".join(tokens)