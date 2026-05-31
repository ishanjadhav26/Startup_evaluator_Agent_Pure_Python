"""
agents/strategy_agent.py
------------------------
Agent 5: Strategy Agent

Responsibilities
----------------
- Design MVP feature set and timeline
- Define revenue model and pricing strategy
- Create go-to-market and customer acquisition plan
- Outline a 36-month growth roadmap

Input  : All previous AgentState outputs
Output : Strategy (written to AgentState.strategy)
"""

from __future__ import annotations

import json

from state import AgentState
from models import Strategy
from tools.llm import LLMTool
from tools.file_manager import FileManager
from logger import get_logger

logger = get_logger("agents.strategy_agent")


class StrategyAgent:
    NAME = "StrategyAgent"

    def __init__(self, llm: LLMTool, file_manager: FileManager) -> None:
        self._llm = llm
        self._fm = file_manager

    def run(self, state: AgentState) -> AgentState:
        logger.info("[%s] Agent started", self.NAME)

        required = ("idea_analysis", "market_research", "competitor_research", "swot_analysis")
        for field in required:
            if not getattr(state, field):
                raise ValueError(f"StrategyAgent requires '{field}' in state")

        # ── Aggregate all prior outputs as context ────────────────────────
        context = {
            "startup_idea": state.startup_idea,
            "idea_analysis": state.idea_analysis.model_dump(),
            "market_research": state.market_research.model_dump(),
            "competitor_research": state.competitor_research.model_dump(),
            "swot_analysis": state.swot_analysis.model_dump(),
        }

        system_prompt = self._fm.load_prompt("strategy")

        user_prompt = (
            "Full Research Context:\n"
            + json.dumps(context, indent=2)
            + "\n\nBuild the business strategy JSON."
        )

        result: Strategy = self._llm.call_structured(
            system_prompt,
            user_prompt,
            Strategy,
            max_tokens=4096,
        )

        state.strategy = result

        logger.info(
            "[%s] Agent completed — MVP weeks=%d | revenue streams=%d | milestones=%d",
            self.NAME,
            result.mvp_timeline_weeks,
            len(result.revenue_streams),
            len(result.key_milestones),
        )
        return state
