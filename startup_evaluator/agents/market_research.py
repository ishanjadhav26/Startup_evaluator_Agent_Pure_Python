"""
agents/market_research.py
-------------------------
Agent 2: Market Research Agent

Responsibilities
----------------
- Research market size (TAM / SAM / SOM)
- Research growth rate and CAGR
- Identify key market trends
- Surface opportunities

Tools  : Tavily Search, LLM
Input  : AgentState.idea_analysis
Output : MarketResearch (written to AgentState.market_research)
"""

from __future__ import annotations

import json

from state import AgentState
from models import MarketResearch
from tools.llm import LLMTool
from tools.tavily_search import TavilySearchTool
from tools.file_manager import FileManager
from logger import get_logger

logger = get_logger("agents.market_research")


class MarketResearchAgent:
    NAME = "MarketResearch"

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
            raise ValueError("MarketResearchAgent requires idea_analysis in state")

        analysis = state.idea_analysis

        # ── Build search queries from idea analysis ────────────────────────
        queries = [
            f"{analysis.industry} market size 2024 2025",
            f"{analysis.industry} market growth rate CAGR",
            f"{analysis.startup_category} {analysis.industry} trends opportunities",
            f"{analysis.target_audience} market size spending",
        ]

        logger.info("[%s] Running %d Tavily searches", self.NAME, len(queries))
        search_responses = self._search.multi_search(queries)

        # ── Format search results as context ──────────────────────────────
        search_context = "\n\n---\n\n".join(
            r.to_context_string() for r in search_responses
        )
        logger.debug("[%s] Search context length: %d chars", self.NAME, len(search_context))

        # ── Load prompt ───────────────────────────────────────────────────
        system_prompt = self._fm.load_prompt("market_research")

        user_prompt = (
            f"Startup Idea: {state.startup_idea}\n\n"
            f"Idea Analysis:\n{json.dumps(analysis.model_dump(), indent=2)}\n\n"
            f"Web Search Results:\n{search_context}\n\n"
            "Based on the above, produce the market research JSON."
        )

        # ── Call LLM ──────────────────────────────────────────────────────
        result: MarketResearch = self._llm.call_structured(
            system_prompt,
            user_prompt,
            MarketResearch,
        )

        state.market_research = result

        logger.info(
            "[%s] Agent completed — TAM=%s | growth=%s | maturity=%s",
            self.NAME,
            result.total_addressable_market,
            result.market_growth_rate,
            result.market_maturity,
        )
        return state
