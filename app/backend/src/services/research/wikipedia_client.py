from __future__ import annotations
import httpx

WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"

async def wiki_summary(topic: str) -> dict | None:
    # Very simple: call summary endpoint (no API key needed)
    topic_enc = topic.strip().replace(" ", "_")
    url = WIKI_SUMMARY + topic_enc
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        if r.status_code != 200:
            return None
        data = r.json()
        return {
            "title": data.get("title"),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
            "content": data.get("extract", "")[:500],
        }