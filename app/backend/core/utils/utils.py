
# core/utils/utils.py
import json, re
from typing import Iterable, List, Union
from core.schemas import Fallacy

def json_load_safe(s: str) -> Union[dict, list]:
    """Best-effort JSON extractor:
    - strips ```json fences
    - extracts first {...} or [...] block
    - returns {} if all attempts fail
    """
    if not s:
        return {}
    t = s.strip()

    # remove common code fences
    if t.startswith("```"):
        # drop ```json\n ... \n```
        t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.IGNORECASE | re.DOTALL).strip()

    # direct load
    try:
        return json.loads(t)
    except Exception:
        pass

    # extract first top-level JSON object/array
    m = re.search(r"(\{.*\}|\[.*\])", t, flags=re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            return {}
    return {}

def _clean_bullet_text(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    for prefix in ("- ", "• ", "* ", "– ", "— "):
        if t.startswith(prefix):
            t = t[len(prefix):].lstrip()
    return t

def format_bullets(bullets: Iterable[str]) -> str:
    if not bullets:
        return ""
    cleaned = [_clean_bullet_text(b) for b in bullets if _clean_bullet_text(b)]
    if not cleaned:
        return ""
    return "".join(f"- {b}\n" for b in cleaned)

def format_ranked(ranked: List[dict]) -> str:
    text = ""
    for c in ranked or []:
        title = (c.get("title") or "").strip()
        why   = (c.get("why") or "").strip()
        if not (title or why):
            continue
        text += f"{title}: {why}\n" if title and why else f"{why}\n"
    return text

def format_fallacies(models: List[Fallacy]) -> str:
    if not models:
        return ""
    lines = ["DETECTED FALLACIES:"]
    seen = set()
    for f in models:
        key = (f.code, f.label, f.why)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"{f.emoji} {f.label}: {f.why}")
    return "\n".join(lines)
