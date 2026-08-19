"""
app/agents/agent.py
~~~~~~~~~~~~~~~~~~~~
Core agent service for Nexora.

This is currently a local, deterministic agent pipeline -- no external
LLM, ML, or paid API is used anywhere in this chain. Each stage is a
placeholder implementation and is expected to be replaced or enhanced in
future phases (e.g. real reasoning, real tool execution, an LLM-backed
understanding/planning step) without changing the overall pipeline
shape:

    task
      -> TaskUnderstanding   (understand the task)
      -> TaskDecomposer      (break it into subtasks)
      -> TaskPlanner         (turn subtasks into a structured plan)
      -> ToolSelector        (resolve the plan's tools)
      -> ToolExecutor        (execute the plan's steps)
      -> ResultVerifier      (verify the execution results)
      -> ResultBuilder       (build the final AgentResult)
"""

from app.agents.decomposition import TaskDecomposer
from app.agents.execution import ToolExecutor
from app.agents.planning import TaskPlanner
from app.agents.result import AgentResult, ResultBuilder
from app.agents.tool_selection import ToolSelector
from app.agents.understanding import TaskUnderstanding
from app.agents.verification import ResultVerifier


class NexoraAgent:
    """The foundation of Nexora's autonomous workflow agent.

    `process_task` runs the full local, deterministic Phase 4 pipeline:
    understanding, decomposition, planning, tool selection, tool
    execution, verification, and final result building. Every stage
    uses local placeholder logic only -- no external LLM, ML, or API
    calls are made anywhere in this chain.
    """

    def __init__(self) -> None:
        self._understanding = TaskUnderstanding()
        self._decomposer = TaskDecomposer()
        self._planner = TaskPlanner()
        self._tool_selector = ToolSelector()
        self._executor = ToolExecutor()
        self._verifier = ResultVerifier()
        self._result_builder = ResultBuilder()

    def process_task(self, task: str) -> AgentResult:
        """Run the full local agent pipeline on a task description.

        Args:
            task: A natural-language description of the task to process.

        Returns:
            The final AgentResult produced by ResultBuilder, describing
            whether the run succeeded and summarizing its execution
            results.

        Raises:
            Exception: If any pipeline component raises an unexpected
                error, it propagates to the caller rather than being
                swallowed or turned into a fake successful result. No
                stack trace is embedded in any returned result object.
        """
        cleaned_task = task.strip()

        understanding = self._understanding.understand(cleaned_task)
        subtasks = self._decomposer.decompose(understanding)
        plan = self._planner.create_plan(subtasks)

        # Tool selection is performed as part of the pipeline so that an
        # unknown tool referenced by the plan is surfaced immediately.
        self._tool_selector.select_tools(plan)

        execution_results = self._executor.execute(plan)
        verification = self._verifier.verify(execution_results)

        return self._result_builder.build(verification, execution_results)