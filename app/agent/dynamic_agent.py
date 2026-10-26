"""Dynamic Agent Compatibility Layer.

Points directly to the unified AlignWorkerAgent engine in app.agent.loop,
ensuring consistent dynamic ReAct planning, verification, and governance
across all interfaces (CLI, Web Studio Dashboard, and REST API).
"""

import os
from typing import Optional, Callable
from app.agent.loop import AlignWorkerAgent, AgentStep, TaskResult

# Type alias for dashboard backwards compatibility
StepRecord = AgentStep
DynamicTaskResult = TaskResult

class DynamicAlignWorker(AlignWorkerAgent):
    """Subclass of AlignWorkerAgent providing seamless compatibility with the studio UI."""

    def __init__(
        self,
        headless: bool = False,
        max_steps: int = 15,
        step_callback: Optional[Callable[[AgentStep], None]] = None
    ):
        port = os.environ.get("PORT", "8000")
        base_url = os.environ.get("PORTAL_BASE_URL", f"http://127.0.0.1:{port}")
        super().__init__(
            base_portal_url=base_url,
            headless_browser=headless,
            hitl_threshold=5000.0,
            auto_approve_hitl=True,
            max_steps=max_steps,
            step_callback=step_callback
        )
