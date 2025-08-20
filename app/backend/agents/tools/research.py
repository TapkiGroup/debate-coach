from typing import List, Dict, Any
from integrations.tavily_client import search as tavily_search
from integrations.wikipedia_client import search_titles, get_summary
import json
from pathlib import Path
from core.llm.main_client import chat as main_chat

_CLASSIFY_PROMPT = Path("prompts/research_classify.txt").read_text(encoding="utf-8")

def gather_sources(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    results = tavily_search(query, max_results=max_results//2) if query else []
    titles = search_titles(query, limit=max_results//2) if query else []
    wiki = [get_summary(t) for t in titles]
    # Deduplicate by URL
    seen = set()
    merged = []
    for it in (results + wiki):
        url = it.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        merged.append(it)
    return merged

def classify_sources(claim: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not sources:
        return []
    blob = json.dumps([{"url": s.get("url",""), "title": s.get("title",""), "snippet": s.get("snippet","")} for s in sources], ensure_ascii=False)
    sys = "Classify sources relative to claim. Reply JSON list."
    user = f"{_CLASSIFY_PROMPT}\n\nCLAIM:\n{claim}\n\nSOURCES:\n{blob}"
    out = main_chat(system=sys, user=user, temperature=0.0, max_tokens=1200)
    try:
        data = json.loads(out)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []
