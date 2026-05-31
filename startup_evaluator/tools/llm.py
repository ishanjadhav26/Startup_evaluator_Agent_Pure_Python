"""
tools/llm.py
------------
Thin wrapper around the OpenAI Chat Completions API.

Features
--------
- Structured JSON output via response_format
- Exponential back-off retry (handles rate limits + transient errors)
- Pydantic model parsing
- Full debug logging of every call
"""

from __future__ import annotations

import json
import time
from typing import Any, Type, TypeVar

from openai import OpenAI, RateLimitError, APIError, APIConnectionError
from pydantic import BaseModel, ValidationError

from config import Config
from logger import get_logger

logger = get_logger("tools.llm")

T = TypeVar("T", bound=BaseModel)

# OpenAI errors that warrant a retry
_RETRYABLE = (RateLimitError, APIConnectionError)


class LLMTool:
    """
    Wraps OpenAI ChatCompletion with:
      - Automatic retry + exponential back-off
      - JSON mode enforcement
      - Pydantic model parsing
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._client = OpenAI(
            api_key=config.groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        logger.debug("LLMTool initialised (model=%s)", config.model_name)

    # ── Public API ────────────────────────────────────────────────────────────

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Call the LLM and return the raw text response.
        Retries up to config.max_retries times with exponential back-off.
        """
        temperature = temperature if temperature is not None else self._config.temperature
        max_tokens = max_tokens if max_tokens is not None else self._config.max_tokens

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(1, self._config.max_retries + 1):
            try:
                logger.debug(
                    "LLM call attempt %d/%d | model=%s | tokens=%d",
                    attempt,
                    self._config.max_retries,
                    self._config.model_name,
                    max_tokens,
                )
                response = self._client.chat.completions.create(
                    model=self._config.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content or ""
                logger.debug("LLM response received (%d chars)", len(content))
                return content

            except _RETRYABLE as exc:
                wait = self._config.retry_base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "Retryable LLM error (attempt %d): %s — retrying in %.1fs",
                    attempt,
                    exc,
                    wait,
                )
                if attempt < self._config.max_retries:
                    time.sleep(wait)
                else:
                    raise

            except APIError as exc:
                logger.error("Non-retryable OpenAI APIError: %s", exc)
                raise

    def call_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        model_class: Type[T],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> T:
        """
        Call the LLM and parse the JSON response into a Pydantic model.
        Falls back to a lenient parser if strict validation fails.
        """
        raw = self.call(
            system_prompt,
            user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # ── Try strict parse ──────────────────────────────────────────────────
        try:
            data = json.loads(raw)
            return model_class.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("Strict parse failed: %s — attempting lenient parse", exc)

        # ── Lenient: strip markdown fences then retry ─────────────────────────
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if clean.endswith("```"):
            clean = clean[: clean.rfind("```")]

        try:
            data = json.loads(clean.strip())
            return model_class.model_validate(data)
        except Exception as exc:
            logger.error(
                "JSON parsing failed for model %s: %s\nRaw output:\n%s",
                model_class.__name__,
                exc,
                raw[:500],
            )
            raise ValueError(
                f"Could not parse LLM output into {model_class.__name__}: {exc}"
            ) from exc

    def call_raw_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Call the LLM and return a plain dict (no Pydantic model)."""
        raw = self.call(system_prompt, user_prompt, temperature=temperature)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse raw JSON: %s", exc)
            raise
