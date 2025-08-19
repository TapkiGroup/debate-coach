from __future__ import annotations
from typing import List
import hashlib
from ...models.schemas import SourceItem, SourceRelation
from .tavily_client import tavily_search
from .wikipedia_client import wiki_summary

NEGATION_HINTS = ("risk", "fail", "problem", "challenge", "criticism", "concern")


def _sid(prefix: str, text: str) -> str:
    return f"{prefix}_{hashlib.md5(text.encode('utf-8')).hexdigest()[:10]}"


def _classify_relation(snippet: str) -> SourceRelation:
    low = (snippet or "").lower()
    if any(tok in low for tok in NEGATION_HINTS):
        return SourceRelation.challenges
    # extremely naive; real system should call GPT-5
    return SourceRelation.supports if len(low) > 0 else SourceRelation.neutral


async def run_research(query: str) -> List[SourceItem]:
    items: List[SourceItem] = []

    # Wikipedia first (if available)
    wiki = await wiki_summary(query)
    if wiki and wiki.get("url"):
        items.append(
            SourceItem(
                id=_sid("SRC", wiki["url"]),
                title=wiki.get("title") or query,
                url=wiki["url"],
                note=(wiki.get("content") or "")[:180],
                relation=SourceRelation.neutral,
            )
        )

    # Tavily results
    results = await tavily_search(query, max_results=5)
    seen = {it.url for it in items}
    for r in results:
        url = r.get("url")
        if not url or url in seen:
            continue
        note = (r.get("content") or "")[:180]
        items.append(
            SourceItem(
                id=_sid("SRC", url),
                title=r.get("title") or url,
                url=url,
                note=note,
                relation=_classify_relation(note),
            )
        )
        seen.add(url)

    return items