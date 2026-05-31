"""
agents/report_generator.py
--------------------------
Agent 6: Report Generator

Responsibilities
----------------
- Compile all prior outputs into a polished Markdown report
- Generate a final GO / CONDITIONAL GO / NO-GO recommendation
- Write the report to reports/startup_report.md

Input  : Full AgentState
Output : Markdown file at reports/startup_report.md
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from state import AgentState
from models import FinalRecommendation
from tools.llm import LLMTool
from tools.file_manager import FileManager
from logger import get_logger

logger = get_logger("agents.report_generator")

_RECOMMENDATION_SYSTEM = """
You are a venture analyst writing the final section of a startup evaluation report.

Based on the complete research provided, produce a final recommendation.
Respond ONLY with a valid JSON object matching this schema:

{
  "verdict": "<GO | CONDITIONAL GO | NO-GO>",
  "confidence": <integer 1–10>,
  "rationale": "<2–3 sentences explaining the verdict>",
  "top_3_priorities": [
    "<priority 1>",
    "<priority 2>",
    "<priority 3>"
  ],
  "biggest_risk": "<single most critical risk>"
}

Return ONLY the JSON object.
"""


class ReportGeneratorAgent:
    NAME = "ReportGenerator"

    def __init__(self, llm: LLMTool, file_manager: FileManager) -> None:
        self._llm = llm
        self._fm = file_manager

    def run(self, state: AgentState) -> AgentState:
        logger.info("[%s] Agent started", self.NAME)

        # ── 1. Generate final recommendation ─────────────────────────────
        rec = self._generate_recommendation(state)
        state.final_recommendation = rec

        # ── 2. Build Markdown report ──────────────────────────────────────
        report_md = self._build_report(state, rec)

        # ── 3. Write to disk ──────────────────────────────────────────────
        path = self._fm.write_report("startup_report.md", report_md)
        state.report_path = str(path)

        logger.info(
            "[%s] Agent completed — verdict=%s | report=%s",
            self.NAME,
            rec.verdict,
            path,
        )
        return state

    # ── Private helpers ───────────────────────────────────────────────────────

    def _generate_recommendation(self, state: AgentState) -> FinalRecommendation:
        context = {
            "startup_idea": state.startup_idea,
            "idea_analysis": state.idea_analysis.model_dump() if state.idea_analysis else {},
            "market_research": state.market_research.model_dump() if state.market_research else {},
            "competitor_research": state.competitor_research.model_dump() if state.competitor_research else {},
            "swot_analysis": state.swot_analysis.model_dump() if state.swot_analysis else {},
            "strategy": state.strategy.model_dump() if state.strategy else {},
        }
        user_prompt = (
            "Complete Evaluation Data:\n"
            + json.dumps(context, indent=2)
            + "\n\nGenerate the final recommendation JSON."
        )
        return self._llm.call_structured(
            _RECOMMENDATION_SYSTEM,
            user_prompt,
            FinalRecommendation,
        )

    def _build_report(self, state: AgentState, rec: FinalRecommendation) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        ia = state.idea_analysis
        mr = state.market_research
        cr = state.competitor_research
        sw = state.swot_analysis
        st = state.strategy

        lines: list[str] = []

        # ─── Title ────────────────────────────────────────────────────────
        lines += [
            "# Startup Evaluation Report",
            f"",
            f"**Idea:** {state.startup_idea}  ",
            f"**Run ID:** `{state.run_id}`  ",
            f"**Generated:** {ts}",
            "",
            "---",
            "",
        ]

        # ─── Executive Summary ────────────────────────────────────────────
        lines += [
            "## 1. Executive Summary",
            "",
            f"> **Verdict: {rec.verdict}** (Confidence: {rec.confidence}/10)",
            "",
            rec.rationale,
            "",
            "**Top 3 Priorities:**",
        ]
        for p in rec.top_3_priorities:
            lines.append(f"- {p}")
        lines += [
            "",
            f"**Biggest Risk:** {rec.biggest_risk}",
            "",
            "---",
            "",
        ]

        # ─── Idea Analysis ────────────────────────────────────────────────
        lines += ["## 2. Idea Analysis", ""]
        if ia:
            lines += [
                f"| Field | Value |",
                f"|---|---|",
                f"| **Industry** | {ia.industry} |",
                f"| **Target Audience** | {ia.target_audience} |",
                f"| **Customer Pain Point** | {ia.customer_pain_point} |",
                f"| **Value Proposition** | {ia.value_proposition} |",
                f"| **Category** | {ia.startup_category} |",
                f"| **Feasibility Score** | {ia.feasibility_score}/10 |",
                "",
                f"**Summary:** {ia.summary}",
                "",
                "**Key Assumptions:**",
            ]
            for a in ia.key_assumptions:
                lines.append(f"- {a}")
        lines += ["", "---", ""]

        # ─── Market Analysis ──────────────────────────────────────────────
        lines += ["## 3. Market Analysis", ""]
        if mr:
            lines += [
                f"| Metric | Value |",
                f"|---|---|",
                f"| **TAM** | {mr.total_addressable_market} |",
                f"| **SAM** | {mr.serviceable_addressable_market} |",
                f"| **SOM** | {mr.serviceable_obtainable_market} |",
                f"| **Growth Rate** | {mr.market_growth_rate} |",
                f"| **Market Maturity** | {mr.market_maturity.title()} |",
                "",
                f"**Summary:** {mr.summary}",
                "",
                "### Key Trends",
            ]
            for t in mr.key_trends:
                icon = "🟢" if t.impact == "positive" else ("🔴" if t.impact == "negative" else "🟡")
                lines += [f"#### {icon} {t.trend}", t.detail, ""]
            lines += ["### Opportunities"]
            for o in mr.opportunities:
                lines.append(f"- {o}")
        lines += ["", "---", ""]

        # ─── Competitor Analysis ──────────────────────────────────────────
        lines += ["## 4. Competitor Analysis", ""]
        if cr:
            lines += [
                f"**Competitive Intensity:** {cr.competitive_intensity.title()}",
                "",
                f"**Summary:** {cr.summary}",
                "",
                "### Direct Competitors",
            ]
            for comp in cr.direct_competitors:
                lines += [
                    f"#### {comp.name}" + (f" — [{comp.website}]({comp.website})" if comp.website else ""),
                    comp.description,
                    "",
                    "**Strengths:**",
                ]
                for s in comp.strengths:
                    lines.append(f"- {s}")
                lines.append("**Weaknesses:**")
                for w in comp.weaknesses:
                    lines.append(f"- {w}")
                if comp.funding_stage:
                    lines.append(f"**Funding:** {comp.funding_stage}")
                if comp.approximate_users_or_revenue:
                    lines.append(f"**Scale:** {comp.approximate_users_or_revenue}")
                lines.append("")

            lines += ["### Indirect Competitors"]
            for comp in cr.indirect_competitors:
                lines += [f"- **{comp.name}:** {comp.description}"]

            lines += ["", "### Market Gaps"]
            for gap in cr.market_gaps:
                lines.append(f"- {gap}")

            lines += ["", "### Differentiation Opportunities"]
            for opp in cr.differentiation_opportunities:
                lines.append(f"- {opp}")
        lines += ["", "---", ""]

        # ─── SWOT Analysis ────────────────────────────────────────────────
        lines += ["## 5. SWOT Analysis", ""]
        if sw:
            lines += [
                f"**Overall Viability:** {sw.overall_viability.title()}  ",
                f"**Key Risk:** {sw.key_risk}",
                "",
                f"**Summary:** {sw.summary}",
                "",
                "| Strengths 💪 | Weaknesses ⚠️ |",
                "|---|---|",
            ]
            max_sw = max(len(sw.strengths), len(sw.weaknesses))
            for i in range(max_sw):
                s = sw.strengths[i] if i < len(sw.strengths) else ""
                w = sw.weaknesses[i] if i < len(sw.weaknesses) else ""
                lines.append(f"| {s} | {w} |")

            lines += [
                "",
                "| Opportunities 🚀 | Threats 🚨 |",
                "|---|---|",
            ]
            max_ot = max(len(sw.opportunities), len(sw.threats))
            for i in range(max_ot):
                o = sw.opportunities[i] if i < len(sw.opportunities) else ""
                t = sw.threats[i] if i < len(sw.threats) else ""
                lines.append(f"| {o} | {t} |")
        lines += ["", "---", ""]

        # ─── Business Strategy ────────────────────────────────────────────
        lines += ["## 6. Business Strategy", ""]
        if st:
            lines += [
                f"**Summary:** {st.summary}",
                "",
                f"### MVP Plan (Est. {st.mvp_timeline_weeks} weeks)",
                "",
                "| Feature | Priority | Rationale |",
                "|---|---|---|",
            ]
            for f in st.mvp_plan:
                lines.append(f"| {f.feature} | {f.priority} | {f.rationale} |")

            lines += ["", "### Revenue Streams", ""]
            for rs in st.revenue_streams:
                arpu = f" — est. ARPU: {rs.estimated_arpu}" if rs.estimated_arpu else ""
                lines.append(f"- **{rs.stream}** ({rs.model}){arpu}")

            lines += [
                "",
                "### Pricing Strategy",
                "",
                st.pricing_strategy,
                "",
                "### Go-To-Market Strategy",
                "",
                st.go_to_market_strategy,
                "",
                "### Customer Acquisition Channels",
            ]
            for ch in st.customer_acquisition_channels:
                lines.append(f"- {ch}")

            lines += [
                "",
                "### Growth Plan",
                "",
                st.growth_plan,
                "",
                "### Key Milestones",
            ]
            for m in st.key_milestones:
                lines.append(f"- {m}")

            if st.burn_rate_estimate:
                lines += ["", f"**Estimated Monthly Burn:** {st.burn_rate_estimate}"]
        lines += ["", "---", ""]

        # ─── Final Recommendation ─────────────────────────────────────────
        lines += [
            "## 7. Final Recommendation",
            "",
            f"### Verdict: {rec.verdict}",
            "",
            f"**Confidence:** {rec.confidence}/10",
            "",
            rec.rationale,
            "",
            "**Top 3 Immediate Priorities:**",
        ]
        for p in rec.top_3_priorities:
            lines.append(f"1. {p}")
        lines += [
            "",
            f"**Critical Risk to Mitigate:** {rec.biggest_risk}",
            "",
            "---",
            "",
            f"*Report generated by Startup Evaluator Agent System — Run ID: `{state.run_id}`*",
        ]

        return "\n".join(lines)
