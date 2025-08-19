from __future__ import annotations
from typing import List
from ..models.schemas import FallacyItem
import re

# Very lightweight heuristics for MVP (to be replaced with GPT reasoning when desired)

COMMON_PATTERNS = [
    (r"\byou are\b", "Ad hominem", "Attacking the person instead of the argument."),
    (r"\balways|never\b", "Hasty generalization", "Over-generalizing from limited cases."),
    (r"\bwhat about\b", "Whataboutism", "Deflecting by raising a different issue."),
]

def detect_fallacies(text: str) -> List[FallacyItem]:
    hits: List[FallacyItem] = []
    low = text.lower()
    for pattern, name, expl in COMMON_PATTERNS:
        if re.search(pattern, low):
            hits.append(FallacyItem(name=name, explanation=expl))
    return hits