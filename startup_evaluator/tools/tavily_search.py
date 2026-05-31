"""
tools/tavily_search.py
----------------------
Wrapper around the Tavily Search API.

Features
--------
- Execute search queries with configurable result count
- Retry with exponential back-off on network / rate-limit errors
- Structured result objects
- Full debug logging
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

import httpx

from config import Config
from logger import get_logger

logger = get_logger("tools.tavily")

_TAVILY_URL = "https://api.tavily.com/search"
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float = 0.0
    published_date: Optional[str] = None


@dataclass
class SearchResponse:
    query: str
    results: List[SearchResult] = field(default_factory=list)
    answer: Optional[str] = None  # Tavily's AI-generated answer (if requested)

    def to_context_string(self) -> str:
        """
        Format results as a readable context block for LLM prompts.
        """
        if not self.results:
            return f"No search results found for: {self.query}"

        lines = [f"Search results for: '{self.query}'\n"]
        for i, r in enumerate(self.results, 1):
            lines.append(f"[{i}] {r.title}")
            lines.append(f"    URL: {r.url}")
            lines.append(f"    {r.content[:400]}")
            lines.append("")
        if self.answer:
            lines.insert(1, f"AI Answer: {self.answer}\n")
        return "\n".join(lines)


class TavilySearchTool:
    """Tavily Search client with retry logic and structured responses."""

    def __init__(self, config: Config) -> None:
        self._api_key = config.tavily_api_key
        self._max_results = config.tavily_max_results
        self._max_retries = config.max_retries
        self._base_delay = config.retry_base_delay
        self._client = httpx.Client(timeout=30.0)
        logger.debug("TavilySearchTool initialised (max_results=%d)", self._max_results)

    # ── Public API ────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        *,
        max_results: Optional[int] = None,
        include_answer: bool = True,
        search_depth: str = "advanced",
    ) -> SearchResponse:
        """
        Run a search query and return a structured SearchResponse.

        Parameters
        ----------
        query          : The natural-language search query.
        max_results    : Override default result count.
        include_answer : Request Tavily's AI summary answer.
        search_depth   : "basic" or "advanced" (advanced = higher quality).
        """
        n = max_results or self._max_results
        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": n,
            "include_answer": include_answer,
            "search_depth": search_depth,
        }

        logger.info("Tavily search: '%s' (depth=%s, n=%d)", query, search_depth, n)

        for attempt in range(1, self._max_retries + 1):
            try:
                resp = self._client.post(_TAVILY_URL, json=payload)

                if resp.status_code in _RETRYABLE_STATUS:
                    wait = self._base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Tavily HTTP %d (attempt %d) — retrying in %.1fs",
                        resp.status_code,
                        attempt,
                        wait,
                    )
                    if attempt < self._max_retries:
                        time.sleep(wait)
                        continue
                    resp.raise_for_status()

                resp.raise_for_status()
                data = resp.json()

                results = [
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        content=r.get("content", ""),
                        score=r.get("score", 0.0),
                        published_date=r.get("published_date"),
                    )
                    for r in data.get("results", [])
                ]

                response = SearchResponse(
                    query=query,
                    results=results,
                    answer=data.get("answer"),
                )
                logger.info(
                    "Tavily returned %d results for '%s'", len(results), query
                )
                logger.debug("Tavily answer: %s", response.answer)
                return response

            except httpx.RequestError as exc:
                wait = self._base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "Tavily network error (attempt %d): %s — retrying in %.1fs",
                    attempt,
                    exc,
                    wait,
                )
                if attempt < self._max_retries:
                    time.sleep(wait)
                else:
                    logger.error("Tavily search failed after %d attempts", self._max_retries)
                    raise

        # Unreachable but satisfies type checker
        return SearchResponse(query=query)

    def multi_search(self, queries: List[str]) -> List[SearchResponse]:
        """Run multiple searches and aggregate results."""
        responses = []
        for q in queries:
            try:
                responses.append(self.search(q))
            except Exception as exc:
                logger.error("Multi-search failed for query '%s': %s", q, exc)
                responses.append(SearchResponse(query=q))  # empty fallback
        return responses

    def __del__(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass
