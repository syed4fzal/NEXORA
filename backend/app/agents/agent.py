"""
app/agents/agent.py
~~~~~~~~~~~~~~~~~~~~
Core agent service for Nexora.

This is currently a local, deterministic agent pipeline -- no external
LLM, ML, or paid API is used anywhere in this chain.
"""

from app.agents.decomposition import TaskDecomposer
from app.agents.execution import ToolExecutor
from app.agents.planning import TaskPlanner
from app.agents.result import AgentResult, ResultBuilder
from app.agents.tool_selection import ToolSelector
from app.agents.understanding import TaskUnderstanding
from app.agents.verification import ResultVerifier


class NexoraAgent:
    """Nexora's local deterministic workflow agent."""

    def __init__(self) -> None:
        self._understanding = TaskUnderstanding()
        self._decomposer = TaskDecomposer()
        self._planner = TaskPlanner()
        self._tool_selector = ToolSelector()
        self._executor = ToolExecutor()
        self._verifier = ResultVerifier()
        self._result_builder = ResultBuilder()

    def process_task(self, task: str) -> AgentResult:
        """Run the complete local Nexora agent pipeline."""

        cleaned_task = task.strip()

        understanding = self._understanding.understand(cleaned_task)
        subtasks = self._decomposer.decompose(understanding)
        plan = self._planner.create_plan(subtasks)

        self._tool_selector.select_tools(plan)

        execution_results = self._executor.execute(plan)
        verification = self._verifier.verify(execution_results)

        return self._result_builder.build(
            verification,
            execution_results,
        )