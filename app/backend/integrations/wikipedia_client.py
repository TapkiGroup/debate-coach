import requests
from typing import List, Dict

SEARCH_URL = "https://en.wikipedia.org/w/api.php"
SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

def search_titles(query: str, limit: int = 3) -> List[str]:
    params = {
        "action": "opensearch",
        "search": query,
        "limit": limit,
        "namespace": 0,
        "format": "json"
    }
    r = requests.get(SEARCH_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    titles = data[1] if isinstance(data, list) and len(data) > 1 else []
    return titles

def get_summary(title: str) -> Dict:
    url = SUMMARY_URL.format(title=title.replace(" ", "_"))
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        return {}
    data = r.json()
    return {
        "title": data.get("title", title),
        "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "snippet": data.get("extract", ""),
    }
