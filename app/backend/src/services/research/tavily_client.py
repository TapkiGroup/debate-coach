from __future__ import annotations
import httpx
from ...core.settings import settings
from ...core.logger import logger

TAVILY_URL = "https://api.tavily.com/search"

async def tavily_search(query: str, max_results: int = 5) -> list[dict]:
    if not settings.tavily_api_key:
        logger.warning("TAVILY_API_KEY missing. Returning dummy tavily results.")
        return [
            {"title": "Example Source A", "url": "https://example.com/a", "content": "Background info supporting some aspects."},
            {"title": "Example Source B", "url": "https://example.com/b", "content": "Critical view challenging assumptions."},
        ]
    async with httpx.AsyncClient(timeout=10) as client:
        payload = {
            "api_key": settings.tavily_api_key,
            "query": query,
            "include_answer": False,
            "search_depth": "basic",
            "max_results": max_results,
        }
        r = await client.post(TAVILY_URL, json=payload)
        r.raise_for_status()
        data = r.json()
        # Expect data like: {"results": [{"title":..., "url":..., "content": ...}, ...]}
        return data.get("results", [])
