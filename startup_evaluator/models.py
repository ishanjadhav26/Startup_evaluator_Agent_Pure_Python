"""
models.py
---------
All Pydantic v2 data models used across the pipeline.
Every agent returns one of these validated objects.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ── Agent 1: Idea Analysis ────────────────────────────────────────────────────

class IdeaAnalysis(BaseModel):
    industry: str = Field(description="Primary industry / vertical")
    target_audience: str = Field(description="Primary customer segment")
    customer_pain_point: str = Field(description="Core problem being solved")
    value_proposition: str = Field(description="Unique value the startup delivers")
    startup_category: str = Field(
        description="Category e.g. SaaS, Marketplace, Consumer App, B2B Tool"
    )
    key_assumptions: List[str] = Field(
        default_factory=list,
        description="Critical assumptions the idea depends on",
    )
    feasibility_score: int = Field(
        ge=1, le=10, description="Initial feasibility score 1–10"
    )
    summary: str = Field(description="1–2 sentence plain-English summary")


# ── Agent 2: Market Research ──────────────────────────────────────────────────

class MarketTrend(BaseModel):
    trend: str
    impact: str  # "positive" | "negative" | "neutral"
    detail: str


class MarketResearch(BaseModel):
    total_addressable_market: str = Field(description="TAM estimate with source hint")
    serviceable_addressable_market: str = Field(description="SAM estimate")
    serviceable_obtainable_market: str = Field(description="SOM estimate")
    market_growth_rate: str = Field(description="CAGR or YoY growth figure")
    key_trends: List[MarketTrend] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    market_maturity: str = Field(
        description="emerging | growing | mature | declining"
    )
    summary: str


# ── Agent 3: Competitor Research ──────────────────────────────────────────────

class Competitor(BaseModel):
    name: str
    website: Optional[str] = None
    description: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    funding_stage: Optional[str] = None
    approximate_users_or_revenue: Optional[str] = None


class CompetitorResearch(BaseModel):
    direct_competitors: List[Competitor] = Field(default_factory=list)
    indirect_competitors: List[Competitor] = Field(default_factory=list)
    market_gaps: List[str] = Field(
        default_factory=list,
        description="Unmet needs or gaps competitors have left open",
    )
    competitive_intensity: str = Field(
        description="low | medium | high | very high"
    )
    differentiation_opportunities: List[str] = Field(default_factory=list)
    summary: str


# ── Agent 4: SWOT Analysis ────────────────────────────────────────────────────

class SWOTAnalysis(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    overall_viability: str = Field(
        description="low | medium | high — overall go/no-go signal"
    )
    key_risk: str = Field(description="Single most important risk to address first")
    summary: str


# ── Agent 5: Strategy ─────────────────────────────────────────────────────────

class MVPFeature(BaseModel):
    feature: str
    priority: str  # "must-have" | "nice-to-have"
    rationale: str


class RevenueStream(BaseModel):
    stream: str
    model: str  # "subscription" | "one-time" | "freemium" | "usage-based" etc.
    estimated_arpu: Optional[str] = None


class Strategy(BaseModel):
    mvp_plan: List[MVPFeature] = Field(default_factory=list)
    mvp_timeline_weeks: int = Field(description="Estimated weeks to ship MVP")
    revenue_streams: List[RevenueStream] = Field(default_factory=list)
    pricing_strategy: str
    go_to_market_strategy: str
    customer_acquisition_channels: List[str] = Field(default_factory=list)
    growth_plan: str
    burn_rate_estimate: Optional[str] = None
    key_milestones: List[str] = Field(default_factory=list)
    summary: str


# ── Report metadata ───────────────────────────────────────────────────────────

class FinalRecommendation(BaseModel):
    verdict: str = Field(description="GO | CONDITIONAL GO | NO-GO")
    confidence: int = Field(ge=1, le=10)
    rationale: str
    top_3_priorities: List[str]
    biggest_risk: str
