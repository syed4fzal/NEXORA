"""
app/agents/agent.py
~~~~~~~~~~~~~~~~~~~

Core agent service for Nexora.

NexoraAgent coordinates the complete local, deterministic workflow:

    User Task
        ↓
    Task Understanding
        ↓
    Task Decomposition
        ↓
    Task Planning
        ↓
    Tool Selection
        ↓
    Tool Execution
        ↓
    Result Verification
        ↓
    Result Building

No LLM, external API, network access, or ML model is used.
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
        # ---------------------------------------------------------
        # Core pipeline components
        # ---------------------------------------------------------

        self._understanding = TaskUnderstanding()
        self._decomposer = TaskDecomposer()
        self._planner = TaskPlanner()
        self._tool_selector = ToolSelector()
        self._executor = ToolExecutor()
        self._verifier = ResultVerifier()
        self._result_builder = ResultBuilder()

    # -------------------------------------------------------------
    # Main agent pipeline
    # -------------------------------------------------------------

    def process_task(self, task: str) -> AgentResult:
        """
        Process a user task through the complete Nexora pipeline.

        Pipeline:

            1. Clean and validate task
            2. Understand task
            3. Decompose into subtasks
            4. Create execution plan
            5. Select tools
            6. Execute tools
            7. Verify results
            8. Build final AgentResult

        Args:
            task:
                Natural-language task provided by the user.

        Returns:
            AgentResult containing the final verified result.

        Raises:
            ValueError:
                If the task is empty.
        """

        # ---------------------------------------------------------
        # STEP 1: Validate and clean input
        # ---------------------------------------------------------

        if not isinstance(task, str):
            raise ValueError(
                "Task must be provided as a string."
            )

        cleaned_task = task.strip()

        if not cleaned_task:
            raise ValueError(
                "Task cannot be empty."
            )

        # ---------------------------------------------------------
        # STEP 2: Understand the task
        # ---------------------------------------------------------

        understanding = (
            self._understanding.understand(
                cleaned_task
            )
        )

        # ---------------------------------------------------------
        # STEP 3: Decompose the task
        # ---------------------------------------------------------

        subtasks = (
            self._decomposer.decompose(
                understanding
            )
        )

        if not subtasks:
            raise ValueError(
                "Unable to decompose the task into subtasks."
            )

        # ---------------------------------------------------------
        # STEP 4: Create execution plan
        # ---------------------------------------------------------

        plan = (
            self._planner.create_plan(
                subtasks
            )
        )

        if not plan.steps:
            raise ValueError(
                "Unable to create an execution plan."
            )

        # ---------------------------------------------------------
        # STEP 5: Select tools
        # ---------------------------------------------------------

        self._tool_selector.select_tools(
            plan
        )

        # ---------------------------------------------------------
        # STEP 6: Execute plan
        # ---------------------------------------------------------

        execution_results = (
            self._executor.execute(
                plan
            )
        )

        # ---------------------------------------------------------
        # STEP 7: Verify execution results
        # ---------------------------------------------------------

        verification = (
            self._verifier.verify(
                execution_results
            )
        )

        # ---------------------------------------------------------
        # STEP 8: Build final result
        # ---------------------------------------------------------

        return self._result_builder.build(
            verification,
            execution_results,
        )