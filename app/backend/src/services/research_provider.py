# FILE: app/backend/src/services/research_provider.py
from __future__ import annotations
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from dataclasses import asdict
import os
import hashlib
import httpx

from ..models.schemas import SourceItem, SourceRelation

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def _sid(prefix: str, text: str) -> str:
    return f"{prefix}_{hashlib.md5(text.encode('utf-8')).hexdigest()[:10]}"

def _wiki_summary(query: str) -> Optional[Dict]:
    topic = quote_plus(query.strip().replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}"
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(url)
            if r.status_code != 200:
                return None
            data = r.json()
            page = data.get("content_urls", {}).get("desktop", {}).get("page")
            if not page:
                return None
            return {
                "title": data.get("title") or query,
                "url": page,
                "content": data.get("extract") or "",
            }
    except Exception:
        return None

def _tavily_search(query: str, max_results: int = 5) -> List[Dict]:
    body: Dict[str, object] = {
        "query": query,
        "include_answer": False,
        "search_depth": "basic",
        "max_results": max_results,
    }
    if TAVILY_API_KEY:
        body["api_key"] = TAVILY_API_KEY
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post("https://api.tavily.com/search", json=body)
            if r.status_code != 200:
                return []
            return r.json().get("results", [])
    except Exception:
        return []

class ResearchProvider:
    """ (Wiki + Tavily)."""

    def search(self, query: str) -> List[Dict]:
        items: List[SourceItem] = []

        # 1) Wikipedia
        wiki = _wiki_summary(query)
        if wiki and wiki.get("url"):
            items.append(
                SourceItem(
                    id=_sid("SRC", wiki["url"]),
                    title=wiki.get("title") or query,
                    url=wiki["url"],
                    note=(wiki.get("content") or "")[:500],
                    relation=SourceRelation.neutral,
                )
            )

        # 2) Tavily
        seen = {it.url for it in items}
        for res in _tavily_search(query, max_results=5):
            url = res.get("url")
            if not url or url in seen:
                continue
            note = (res.get("content") or "")[:180]
            items.append(
                SourceItem(
                    id=_sid("SRC", url),
                    title=res.get("title") or url,
                    url=url,
                    note=note,
                    relation=SourceRelation.neutral,
                )
            )
            seen.add(url)

        return [it.model_dump() for it in items]
