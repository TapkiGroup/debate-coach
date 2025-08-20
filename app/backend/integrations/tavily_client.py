import os, requests
from typing import List, Dict, Any
from core.config import settings

API_URL = "https://api.tavily.com/search"

def search(query: str, max_results: int = 6) -> List[Dict[str, Any]]:
    if not settings.TAVILY_API_KEY:
        return []
    payload = {
        "api_key": settings.TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_answer": False,
        "max_results": max_results,
    }
    r = requests.post(API_URL, json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    out = []
    for it in results:
        out.append({
            "title": it.get("title") or it.get("url"),
            "url": it.get("url"),
            "snippet": it.get("content") or it.get("snippet") or "",
        })
    return out
