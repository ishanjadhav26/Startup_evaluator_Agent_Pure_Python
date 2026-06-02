"""
config.py
---------
Centralised configuration: loads and validates all environment variables.
Raises clear errors on startup when required keys are missing.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root (safe no-op if absent)
load_dotenv()

BASE_DIR: Path = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Config:
    # ── API Keys ────────────────────────────────────────────────────────────
    groq_api_key: str = field(default_factory=lambda: os.environ.get("GROQ_API_KEY", ""))
    tavily_api_key: str = field(default_factory=lambda: os.environ.get("TAVILY_API_KEY", ""))

    # ── Model ────────────────────────────────────────────────────────────────
    model_name: str = field(
        default_factory=lambda: os.getenv("MODEL_NAME", "llama-3.1-8b-instant")
    )
    temperature: float = field(
        default_factory=lambda: float(os.getenv("TEMPERATURE", "0.3"))
    )
    max_tokens: int = field(
        default_factory=lambda: int(os.getenv("MAX_TOKENS", "4096"))
    )

    # ── Retry / Back-off ─────────────────────────────────────────────────────
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("MAX_RETRIES", "3"))
    )
    retry_base_delay: float = field(
        default_factory=lambda: float(os.getenv("RETRY_BASE_DELAY", "1.0"))
    )

    # ── Tavily ───────────────────────────────────────────────────────────────
    tavily_max_results: int = field(
        default_factory=lambda: int(os.getenv("TAVILY_MAX_RESULTS", "5"))
    )

    # ── Paths ────────────────────────────────────────────────────────────────
    prompts_dir: Path = field(default_factory=lambda: BASE_DIR / "prompts")
    reports_dir: Path = field(default_factory=lambda: BASE_DIR / "reports")
    logs_dir: Path = field(default_factory=lambda: BASE_DIR / "logs")
    memory_dir: Path = field(default_factory=lambda: BASE_DIR / "memory")

    def validate(self) -> None:
        """Raise ValueError for any missing required field."""
        missing = []
        if not self.groq_api_key:
            missing.append("GROQ_API_KEY")
        if not self.tavily_api_key:
            missing.append("TAVILY_API_KEY")
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Copy .env.example to .env and fill in your keys."
            )

    def ensure_dirs(self) -> None:
        """Create output directories if they don't exist."""
        for d in (self.reports_dir, self.logs_dir, self.memory_dir):
            d.mkdir(parents=True, exist_ok=True)


def get_config() -> Config:
    cfg = Config()
    cfg.validate()
    cfg.ensure_dirs()
    return cfg
