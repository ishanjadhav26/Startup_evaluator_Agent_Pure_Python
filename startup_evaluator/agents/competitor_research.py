"""
agents/competitor_research.py
------------------------------
Agent 3: Competitor Research Agent

Responsibilities
----------------
- Find direct and indirect competitors
- Analyse strengths / weaknesses per competitor
- Identify market gaps and differentiation opportunities

Tools  : Tavily Search, LLM
Input  : AgentState.idea_analysis
Output : CompetitorResearch (written to AgentState.competitor_research)
"""

from __future__ import annotations

import json

from state import AgentState
from models import CompetitorResearch
from tools.llm import LLMTool
from tools.tavily_search import TavilySearchTool
from tools.file_manager import FileManager
from logger import get_logger

logger = get_logger("agents.competitor_research")


class CompetitorResearchAgent:
    NAME = "CompetitorResearch"

    def __init__(
        self,
        llm: LLMTool,
        search: TavilySearchTool,
        file_manager: FileManager,
    ) -> None:
        self._llm = llm
        self._search = search
        self._fm = file_manager

    def run(self, state: AgentState) -> AgentState:
        logger.info("[%s] Agent started", self.NAME)

        if not state.idea_analysis:
            raise ValueError("CompetitorResearchAgent requires idea_analysis in state")

        analysis = state.idea_analysis

        # ── Build targeted competitor search queries ───────────────────────
        queries = [
            f"{analysis.industry} {analysis.startup_category} startups competitors 2024",
            f"best apps for {analysis.target_audience} {analysis.industry}",
            f"{analysis.startup_category} {analysis.customer_pain_point} solutions",
            f"{analysis.industry} startups funding series A B 2023 2024",
            f"alternatives to {analysis.industry.lower()} tools for {analysis.target_audience}",
        ]

        logger.info("[%s] Running %d Tavily searches", self.NAME, len(queries))
        search_responses = self._search.multi_search(queries)

        search_context = "\n\n---\n\n".join(
            r.to_context_string() for r in search_responses
        )
        logger.debug("[%s] Search context length: %d chars", self.NAME, len(search_context))

        # ── Load prompt ───────────────────────────────────────────────────
        system_prompt = self._fm.load_prompt("competitor_research")

        user_prompt = (
            f"Startup Idea: {state.startup_idea}\n\n"
            f"Idea Analysis:\n{json.dumps(analysis.model_dump(), indent=2)}\n\n"
            f"Web Search Results:\n{search_context}\n\n"
            "Based on the above, produce the competitor research JSON."
        )

        # ── Call LLM ──────────────────────────────────────────────────────
        result: CompetitorResearch = self._llm.call_structured(
            system_prompt,
            user_prompt,
            CompetitorResearch,
        )

        state.competitor_research = result

        logger.info(
            "[%s] Agent completed — direct=%d | indirect=%d | intensity=%s",
            self.NAME,
            len(result.direct_competitors),
            len(result.indirect_competitors),
            result.competitive_intensity,
        )
        return state
