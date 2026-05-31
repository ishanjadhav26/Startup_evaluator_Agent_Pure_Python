"""
logger.py
---------
Configures a structured logger that writes to:
  - Console  (INFO level, coloured via logging.Formatter)
  - logs/agent.log  (DEBUG level, rotating, JSON-style lines)
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_initialised = False


def setup_logging(logs_dir: Path, level: int = logging.DEBUG) -> None:
    """Call once at application start-up."""
    global _initialised
    if _initialised:
        return

    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "agent.log"

    root = logging.getLogger()
    root.setLevel(level)

    # ── File handler (DEBUG, rotating 5 MB × 3 files) ───────────────────────
    fh = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(fh)

    # ── Console handler (INFO) ───────────────────────────────────────────────
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(ch)

    _initialised = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
