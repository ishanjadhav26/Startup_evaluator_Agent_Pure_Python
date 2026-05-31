"""
agents/swot_agent.py
--------------------
Agent 4: SWOT Analysis Agent

Responsibilities
----------------
- Synthesise Idea Analysis + Market Research + Competitor Research
- Produce a structured SWOT (Strengths, Weaknesses, Opportunities, Threats)
- Assign overall viability rating
- Flag the single most critical risk

Input  : idea_analysis, market_research, competitor_research (all from state)
Output : SWOTAnalysis (written to AgentState.swot_analysis)
"""

from __future__ import annotations

import json

from state import AgentState
from models import SWOTAnalysis
from tools.llm import LLMTool
from tools.file_manager import FileManager
from logger import get_logger

logger = get_logger("agents.swot_agent")


class SWOTAgent:
    NAME = "SWOTAgent"

    def __init__(self, llm: LLMTool, file_manager: FileManager) -> None:
        self._llm = llm
        self._fm = file_manager

    def run(self, state: AgentState) -> AgentState:
        logger.info("[%s] Agent started", self.NAME)

        for field in ("idea_analysis", "market_research", "competitor_research"):
            if not getattr(state, field):
                raise ValueError(f"SWOTAgent requires '{field}' in state")

        # ── Build rich context from prior outputs ─────────────────────────
        context = {
            "startup_idea": state.startup_idea,
            "idea_analysis": state.idea_analysis.model_dump(),
            "market_research": state.market_research.model_dump(),
            "competitor_research": state.competitor_research.model_dump(),
        }

        system_prompt = self._fm.load_prompt("swot")

        user_prompt = (
            "Research Inputs:\n"
            + json.dumps(context, indent=2)
            + "\n\nProduce the SWOT analysis JSON."
        )

        result: SWOTAnalysis = self._llm.call_structured(
            system_prompt,
            user_prompt,
            SWOTAnalysis,
        )

        state.swot_analysis = result

        logger.info(
            "[%s] Agent completed — viability=%s | strengths=%d | threats=%d",
            self.NAME,
            result.overall_viability,
            len(result.strengths),
            len(result.threats),
        )
        return state
