"""
agents/idea_analyzer.py
-----------------------
Agent 1: Idea Analyzer

Responsibilities
----------------
- Identify industry, target audience, pain point, value proposition, category
- Assess feasibility
- Extract key assumptions

Input  : startup_idea (str)
Output : IdeaAnalysis (written to AgentState.idea_analysis)
"""

from __future__ import annotations

from state import AgentState
from models import IdeaAnalysis
from tools.llm import LLMTool
from tools.file_manager import FileManager
from logger import get_logger

logger = get_logger("agents.idea_analyzer")


class IdeaAnalyzerAgent:
    NAME = "IdeaAnalyzer"

    def __init__(self, llm: LLMTool, file_manager: FileManager) -> None:
        self._llm = llm
        self._fm = file_manager

    def run(self, state: AgentState) -> AgentState:
        logger.info("[%s] Agent started — idea: '%s'", self.NAME, state.startup_idea[:80])

        # ── Load prompt ───────────────────────────────────────────────────────
        system_prompt = self._fm.load_prompt("idea_analyzer")

        user_prompt = (
            f"Startup Idea:\n{state.startup_idea}\n\n"
            "Analyse this idea and return the structured JSON as specified."
        )

        # ── Call LLM ──────────────────────────────────────────────────────────
        result: IdeaAnalysis = self._llm.call_structured(
            system_prompt,
            user_prompt,
            IdeaAnalysis,
        )

        # ── Persist to state ──────────────────────────────────────────────────
        state.idea_analysis = result

        logger.info(
            "[%s] Agent completed — industry=%s | score=%d/10",
            self.NAME,
            result.industry,
            result.feasibility_score,
        )
        return state
