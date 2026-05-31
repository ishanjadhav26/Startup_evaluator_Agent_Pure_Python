"""
tools/file_manager.py
---------------------
Handles all file I/O for the pipeline:
  - Loading prompt templates from the prompts/ directory
  - Writing the final Markdown report to reports/
  - Helper for safe file reads/writes
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from logger import get_logger

logger = get_logger("tools.file_manager")


class FileManager:
    def __init__(self, prompts_dir: Path, reports_dir: Path) -> None:
        self._prompts_dir = prompts_dir
        self._reports_dir = reports_dir
        self._reports_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(
            "FileManager ready (prompts=%s, reports=%s)",
            prompts_dir,
            reports_dir,
        )

    # ── Prompts ───────────────────────────────────────────────────────────────

    def load_prompt(self, name: str) -> str:
        """
        Load a prompt template by name (with or without .txt extension).
        Raises FileNotFoundError with a clear message if missing.
        """
        filename = name if name.endswith(".txt") else f"{name}.txt"
        path = self._prompts_dir / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {path}\n"
                f"Available prompts: {[p.name for p in self._prompts_dir.glob('*.txt')]}"
            )

        content = path.read_text(encoding="utf-8").strip()
        logger.debug("Loaded prompt '%s' (%d chars)", filename, len(content))
        return content

    # ── Reports ───────────────────────────────────────────────────────────────

    def write_report(self, filename: str, content: str) -> Path:
        """Write a report file to the reports directory."""
        path = self._reports_dir / filename
        path.write_text(content, encoding="utf-8")
        logger.info("Report written: %s", path)
        return path

    def read_report(self, filename: str) -> Optional[str]:
        """Read a report file; return None if it doesn't exist."""
        path = self._reports_dir / filename
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    # ── Generic helpers ───────────────────────────────────────────────────────

    @staticmethod
    def write_text(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.debug("Wrote file: %s (%d bytes)", path, len(content.encode()))

    @staticmethod
    def read_text(path: Path) -> Optional[str]:
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")
