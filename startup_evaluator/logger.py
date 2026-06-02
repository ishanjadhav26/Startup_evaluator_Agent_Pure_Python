"""
logger.py
---------
Configures a structured logger that writes to:
  - Console  (INFO level, coloured via logging.Formatter)
  - logs/agent.log  (DEBUG level, rotating, JSON-style lines)
"""

import logging
import sys
import io
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Force UTF-8 output on Windows to avoid UnicodeEncodeError with special chars (✔ ✘ etc.)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


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

    # ── Memory handler for Web (INFO) ────────────────────────────────────────
    mh = MemoryLogHandler()
    mh.setLevel(logging.INFO)
    mh.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(mh)

    _initialised = True


import contextvars

# Context variable to store current run_id
current_run_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_run_id", default=None)

# Global store for logs: run_id -> list of log strings
run_logs: dict[str, list[str]] = {}

class MemoryLogHandler(logging.Handler):
    """Intercepts logs and stores them in `run_logs` mapped by `current_run_id`."""
    def emit(self, record: logging.LogRecord) -> None:
        run_id = current_run_id.get()
        if not run_id:
            return
        
        try:
            msg = self.format(record)
            if run_id not in run_logs:
                run_logs[run_id] = []
            run_logs[run_id].append(msg)
        except Exception:
            self.handleError(record)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
