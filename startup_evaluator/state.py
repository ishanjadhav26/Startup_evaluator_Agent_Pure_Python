"""
state.py
--------
Single source of truth for the entire pipeline run.
Agents read from and write to this object; no framework magic needed.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from models import (
    IdeaAnalysis,
    MarketResearch,
    CompetitorResearch,
    SWOTAnalysis,
    Strategy,
    FinalRecommendation,
)


class AgentState(BaseModel):
    """Shared state passed sequentially through every agent."""

    # ── Run identity ─────────────────────────────────────────────────────────
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # ── Input ─────────────────────────────────────────────────────────────────
    startup_idea: str

    # ── Agent outputs (populated one by one) ─────────────────────────────────
    idea_analysis: Optional[IdeaAnalysis] = None
    market_research: Optional[MarketResearch] = None
    competitor_research: Optional[CompetitorResearch] = None
    swot_analysis: Optional[SWOTAnalysis] = None
    strategy: Optional[Strategy] = None
    final_recommendation: Optional[FinalRecommendation] = None

    # ── Report path ───────────────────────────────────────────────────────────
    report_path: Optional[str] = None

    # ── Pipeline status ───────────────────────────────────────────────────────
    status: str = "pending"   # pending | running | completed | failed
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def mark_running(self) -> None:
        self.status = "running"

    def mark_completed(self) -> None:
        self.status = "completed"

    def mark_failed(self, error: str) -> None:
        self.status = "failed"
        self.error = error

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
