"""
main.py
-------
Entry point for the Startup Idea Evaluation Agent System.

Pipeline
--------
  Input idea
       │
  [Agent 1] IdeaAnalyzer
       │
  [Agent 2] MarketResearch  (+ Tavily)
       │
  [Agent 3] CompetitorResearch  (+ Tavily)
       │
  [Agent 4] SWOTAgent
       │
  [Agent 5] StrategyAgent
       │
  [Agent 6] ReportGenerator
       │
  reports/startup_report.md

Usage
-----
  python main.py "AI Interview Preparation Platform for College Students"
  python main.py  # prompts interactively
"""

from __future__ import annotations

import sys
import time
import traceback

from config import get_config
from logger import setup_logging, get_logger
from state import AgentState
from tools.llm import LLMTool
from tools.tavily_search import TavilySearchTool
from tools.file_manager import FileManager
from agents.idea_analyzer import IdeaAnalyzerAgent
from agents.market_research import MarketResearchAgent
from agents.competitor_research import CompetitorResearchAgent
from agents.swot_agent import SWOTAgent
from agents.strategy_agent import StrategyAgent
from agents.report_generator import ReportGeneratorAgent
import memory as mem


def run_pipeline(startup_idea: str) -> AgentState:
    """
    Execute the full 6-agent evaluation pipeline for the given startup idea.
    Returns the final AgentState (regardless of success/failure).
    """
    # ── Bootstrap ─────────────────────────────────────────────────────────────
    config = get_config()
    setup_logging(config.logs_dir)
    logger = get_logger("main")

    logger.info("=" * 60)
    logger.info("Startup Evaluator — Pipeline starting")
    logger.info("Idea: %s", startup_idea[:120])
    logger.info("Model: %s", config.model_name)
    logger.info("=" * 60)

    # ── Initialise shared tools ───────────────────────────────────────────────
    llm = LLMTool(config)
    search = TavilySearchTool(config)
    fm = FileManager(config.prompts_dir, config.reports_dir)

    # ── Initialise agents ─────────────────────────────────────────────────────
    agents = [
        IdeaAnalyzerAgent(llm, fm),
        MarketResearchAgent(llm, search, fm),
        CompetitorResearchAgent(llm, search, fm),
        SWOTAgent(llm, fm),
        StrategyAgent(llm, fm),
        ReportGeneratorAgent(llm, fm),
    ]

    # ── Build initial state ───────────────────────────────────────────────────
    state = AgentState(startup_idea=startup_idea)
    state.mark_running()

    # ── Run each agent sequentially ───────────────────────────────────────────
    total_start = time.perf_counter()

    for agent in agents:
        agent_start = time.perf_counter()
        logger.info("► Running %s ...", agent.NAME)
        try:
            state = agent.run(state)
            elapsed = time.perf_counter() - agent_start
            logger.info("✔ %s completed in %.1fs", agent.NAME, elapsed)
        except Exception as exc:
            elapsed = time.perf_counter() - agent_start
            logger.error(
                "✘ %s failed after %.1fs: %s\n%s",
                agent.NAME,
                elapsed,
                exc,
                traceback.format_exc(),
            )
            state.mark_failed(str(exc))
            break

    # ── Finalise ──────────────────────────────────────────────────────────────
    total_elapsed = time.perf_counter() - total_start

    if state.status != "failed":
        state.mark_completed()

    logger.info("=" * 60)
    logger.info(
        "Pipeline %s in %.1fs | Run ID: %s",
        state.status.upper(),
        total_elapsed,
        state.run_id,
    )
    if state.report_path:
        logger.info("Report: %s", state.report_path)
    if state.error:
        logger.error("Error: %s", state.error)
    logger.info("=" * 60)

    # ── Persist to memory ─────────────────────────────────────────────────────
    try:
        mem.save_memory(state.to_dict())
    except Exception as exc:
        logger.warning("Failed to save memory: %s", exc)

    return state


def main() -> None:
    # ── Get startup idea from CLI arg or interactive prompt ───────────────────
    if len(sys.argv) > 1:
        idea = " ".join(sys.argv[1:])
    else:
        print("\n🚀 Startup Idea Evaluation Agent System")
        print("─" * 40)
        idea = input("Enter your startup idea: ").strip()
        if not idea:
            print("No idea provided. Exiting.")
            sys.exit(1)

    print(f"\n📋 Evaluating: '{idea}'\n")
    print("This may take 1–2 minutes while agents research and analyse...\n")

    state = run_pipeline(idea)

    # ── Print summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if state.status == "completed":
        rec = state.final_recommendation
        print(f"✅ EVALUATION COMPLETE")
        print(f"   Verdict   : {rec.verdict if rec else 'N/A'}")
        print(f"   Confidence: {rec.confidence}/10" if rec else "")
        print(f"   Report    : {state.report_path}")
    else:
        print(f"❌ EVALUATION FAILED")
        print(f"   Error: {state.error}")
    print("=" * 60 + "\n")

    if state.status != "completed":
        sys.exit(1)


if __name__ == "__main__":
    main()
