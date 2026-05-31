# 🚀 Startup Idea Evaluation Agent System

A **production-ready, multi-agent pipeline** built in **pure Python** (no agent frameworks) that takes a startup idea and produces a comprehensive business evaluation report.

---

## Architecture

```
Input Idea
    │
    ▼
┌─────────────────────┐
│  Agent 1            │  IdeaAnalyzerAgent
│  Idea Analyzer      │  → Identifies industry, audience, pain point, value prop
└────────┬────────────┘
         │ IdeaAnalysis (JSON)
         ▼
┌─────────────────────┐
│  Agent 2            │  MarketResearchAgent + Tavily Search
│  Market Research    │  → TAM/SAM/SOM, growth rate, trends, opportunities
└────────┬────────────┘
         │ MarketResearch (JSON)
         ▼
┌─────────────────────┐
│  Agent 3            │  CompetitorResearchAgent + Tavily Search
│  Competitor Intel   │  → Direct/indirect competitors, gaps, differentiation
└────────┬────────────┘
         │ CompetitorResearch (JSON)
         ▼
┌─────────────────────┐
│  Agent 4            │  SWOTAgent
│  SWOT Analysis      │  → Strengths, Weaknesses, Opportunities, Threats
└────────┬────────────┘
         │ SWOTAnalysis (JSON)
         ▼
┌─────────────────────┐
│  Agent 5            │  StrategyAgent
│  Business Strategy  │  → MVP plan, revenue model, GTM, growth roadmap
└────────┬────────────┘
         │ Strategy (JSON)
         ▼
┌─────────────────────┐
│  Agent 6            │  ReportGeneratorAgent
│  Report Generator   │  → Final verdict + Markdown report
└─────────────────────┘
         │
         ▼
  reports/startup_report.md
```

---

## Project Structure

```
startup_evaluator/
├── agents/
│   ├── idea_analyzer.py        # Agent 1
│   ├── market_research.py      # Agent 2
│   ├── competitor_research.py  # Agent 3
│   ├── swot_agent.py           # Agent 4
│   ├── strategy_agent.py       # Agent 5
│   └── report_generator.py     # Agent 6
│
├── tools/
│   ├── llm.py                  # OpenAI wrapper (retry, JSON parsing)
│   ├── tavily_search.py        # Tavily Search wrapper (retry, structured results)
│   └── file_manager.py         # Prompt loading, report writing
│
├── prompts/                    # All system prompts (loaded at runtime)
│   ├── idea_analyzer.txt
│   ├── market_research.txt
│   ├── competitor_research.txt
│   ├── swot.txt
│   └── strategy.txt
│
├── memory/
│   └── __init__.py             # save_memory() / load_memory() → history.json
│
├── reports/                    # Generated reports (volume-mounted in Docker)
├── logs/                       # agent.log (volume-mounted in Docker)
│
├── state.py                    # AgentState — shared across all agents
├── config.py                   # Environment variable loading + validation
├── logger.py                   # Rotating file + console logger
├── models.py                   # Pydantic v2 models for every agent output
├── main.py                     # Pipeline orchestrator / entry point
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Prerequisites

- Python 3.11+
- [OpenAI API key](https://platform.openai.com/api-keys)
- [Tavily API key](https://app.tavily.com) (free tier available)
- Docker + Docker Compose (optional, for containerised run)

---

## Quick Start

### 1 · Clone and configure

```bash
git clone <repo-url>
cd startup_evaluator

cp .env.example .env
# Edit .env and fill in OPENAI_API_KEY and TAVILY_API_KEY
```

### 2 · Run locally (Python venv)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Pass idea as CLI argument
python main.py "AI Interview Preparation Platform for College Students"

# Or run interactively
python main.py
```

### 3 · Run with Docker

```bash
# Build and run (default idea in docker-compose.yml)
docker compose up --build

# Run with a custom idea
docker compose run startup-evaluator "On-demand home cleaning marketplace"

# View the generated report
cat reports/startup_report.md
```

---

## Output

The pipeline writes `reports/startup_report.md` containing:

| Section | Contents |
|---|---|
| Executive Summary | Verdict (GO / CONDITIONAL GO / NO-GO) + confidence |
| Idea Analysis | Industry, audience, pain point, value prop, feasibility |
| Market Analysis | TAM/SAM/SOM, growth rate, trends, opportunities |
| Competitor Analysis | Direct + indirect competitors, gaps, differentiation |
| SWOT Analysis | 4×4 grid with viability rating |
| Business Strategy | MVP plan, revenue model, GTM, growth roadmap |
| Final Recommendation | Verdict, top 3 priorities, biggest risk |

---

## Configuration

All settings via environment variables (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Required |
| `TAVILY_API_KEY` | — | Required |
| `MODEL_NAME` | `gpt-4o-mini` | OpenAI model |
| `TEMPERATURE` | `0.3` | LLM temperature |
| `MAX_TOKENS` | `4096` | Max tokens per call |
| `MAX_RETRIES` | `3` | Retry attempts |
| `RETRY_BASE_DELAY` | `1.0` | Back-off base (seconds) |
| `TAVILY_MAX_RESULTS` | `5` | Search results per query |

---

## Memory

Each pipeline run is appended to `memory/history.json`. Access programmatically:

```python
import memory as mem

history = mem.load_memory()        # All past runs
last = mem.get_last_evaluation()   # Most recent run
mem.clear_memory()                 # Wipe history
```

---

## Extending the System

**Add a new agent:**
1. Create `agents/your_agent.py` with a class that has a `run(state) -> state` method
2. Add a new Pydantic model in `models.py`
3. Add the field to `AgentState` in `state.py`
4. Create the prompt in `prompts/your_agent.txt`
5. Insert the agent into the pipeline list in `main.py`

**Swap the LLM:**
Edit `tools/llm.py` — the `LLMTool` class is self-contained. Replace the OpenAI client with any provider that returns JSON.

**Swap the search tool:**
Edit `tools/tavily_search.py` or create a new class implementing the same `search()` interface.

---

## Logs

Logs are written to `logs/agent.log` (rotating, 5 MB × 3 files):

```
2024-01-15 10:23:01 | INFO     | agents.idea_analyzer    | [IdeaAnalyzer] Agent started
2024-01-15 10:23:02 | INFO     | agents.idea_analyzer    | [IdeaAnalyzer] Agent completed — industry=EdTech | score=8/10
2024-01-15 10:23:02 | INFO     | agents.market_research  | Tavily search: 'EdTech market size 2024 2025'
```

---

## License

MIT
