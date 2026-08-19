"""
app/agents/tool_selection.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Local Tool Selection component for Nexora.

Defines the registry of tools currently known to Nexora and a selector
that maps a TaskPlan's steps onto their corresponding ToolDefinition
objects. No tool is actually executed here -- these are definitions
only, and this component is not yet wired into NexoraAgent.
"""

from dataclasses import dataclass

from app.agents.planning import TaskPlan


@dataclass
class ToolDefinition:
    """A definition of a tool known to Nexora (no execution logic yet)."""

    name: str
    description: str
    available: bool = True


class ToolRegistry:
    """A local registry of the tools currently available to Nexora.

    These are definitions only -- no tool functionality is implemented
    at this stage.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {
            tool.name: tool for tool in self._build_default_tools()
        }

    @staticmethod
    def _build_default_tools() -> list[ToolDefinition]:
        """Build the default set of known tool definitions."""
        return [
            ToolDefinition(name="data_loader", description="Loads raw data for processing."),
            ToolDefinition(name="data_inspector", description="Inspects loaded data."),
            ToolDefinition(
                name="data_analyzer", description="Analyzes data, e.g. for unusual transactions."
            ),
            ToolDefinition(name="document_reader", description="Reads a document's contents."),
            ToolDefinition(
                name="document_extractor", description="Extracts important information from a document."
            ),
            ToolDefinition(name="document_summarizer", description="Summarizes a document."),
            ToolDefinition(
                name="report_generator", description="Prepares a summary/report of findings."
            ),
            ToolDefinition(
                name="general_processor", description="Handles tasks with no specific tool match."
            ),
        ]

    def get(self, name: str) -> ToolDefinition | None:
        """Look up a tool definition by name, or return None if unknown."""
        return self._tools.get(name)

    def all_tools(self) -> list[ToolDefinition]:
        """Return every registered tool definition."""
        return list(self._tools.values())


class ToolSelector:
    """Selects the tool definitions required to execute a TaskPlan.

    This is a placeholder for a future, more capable tool-selection
    system. It only looks up tools by name in the ToolRegistry -- it
    does not execute anything.
    """

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self._registry = registry or ToolRegistry()

    def select_tools(self, plan: TaskPlan) -> list[ToolDefinition]:
        """Select the tool definitions referenced by a plan's steps.

        Args:
            plan: A TaskPlan produced by TaskPlanner.create_plan().

        Returns:
            The ToolDefinition objects referenced by the plan's steps,
            in step order, with duplicates removed (first occurrence
            kept).

        Raises:
            ValueError: If a step references a tool name that is not
                registered in the ToolRegistry.
        """
        selected: list[ToolDefinition] = []
        seen_names: set[str] = set()

        for step in plan.steps:
            if step.tool in seen_names:
                continue

            tool = self._registry.get(step.tool)
            if tool is None:
                raise ValueError(f"Unknown tool: {step.tool}")

            selected.append(tool)
            seen_names.add(step.tool)

        return selected