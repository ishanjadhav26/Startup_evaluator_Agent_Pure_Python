"""
memory/__init__.py
------------------
Provides save_memory() and load_memory() backed by a local JSON file.
Each entry captures the complete AgentState for one pipeline run,
allowing the user to review past evaluations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from logger import get_logger

logger = get_logger("memory")

_HISTORY_FILE = Path(__file__).resolve().parent / "history.json"


# ── Public API ────────────────────────────────────────────────────────────────

def save_memory(state_dict: Dict[str, Any]) -> None:
    """
    Append the serialised AgentState dict to history.json.
    Creates the file if it doesn't exist.
    """
    history = _load_raw()
    history.append(state_dict)

    _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _HISTORY_FILE.write_text(
        json.dumps(history, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info(
        "Memory saved (run_id=%s, total_runs=%d)",
        state_dict.get("run_id", "?"),
        len(history),
    )


def load_memory() -> List[Dict[str, Any]]:
    """
    Load the full evaluation history.
    Returns an empty list if history.json doesn't exist yet.
    """
    history = _load_raw()
    logger.debug("Loaded %d historical evaluations from memory", len(history))
    return history


def get_last_evaluation() -> Optional[Dict[str, Any]]:
    """Return the most recent evaluation, or None."""
    history = _load_raw()
    return history[-1] if history else None


def clear_memory() -> None:
    """Wipe the history file."""
    if _HISTORY_FILE.exists():
        _HISTORY_FILE.unlink()
        logger.warning("Memory cleared — history.json deleted")


# ── Internal ──────────────────────────────────────────────────────────────────

def _load_raw() -> List[Dict[str, Any]]:
    if not _HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError as exc:
        logger.error("Corrupt history.json: %s — returning empty history", exc)
        return []
