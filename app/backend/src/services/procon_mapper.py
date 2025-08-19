from __future__ import annotations
import hashlib
from typing import Tuple, List
from ..models.schemas import ProConItem, FallacyItem
from .fallacy_detector import detect_fallacies


def _mk_id(prefix: str, text: str) -> str:
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{h}"


def strengthen_and_map(message: str) -> Tuple[str, List[ProConItem], List[ProConItem]]:
    """
    Simplified heuristic: create a clearer headline and split into bullets.
    In production, delegate to GPT-5 to produce steel-man PRO and best-case CON.
    """
    msg = message.strip()
    # Naive strengthening: ensure a crisp title
    title = msg.split(".\n")[0][:120]
    if len(title) < 10:
        title = f"Refined claim: {title}"

    # Prototype bullets
    pro_bullets = [
        ProConItem(id=_mk_id("PRO", f"{title}-pro1"), title=title, body="Refined supporting point 1."),
        ProConItem(id=_mk_id("PRO", f"{title}-pro2"), title=f"Further support: {title}", body="Supporting point 2."),
    ]

    fallacies: List[FallacyItem] = detect_fallacies(msg)
    con_bullets = [
        ProConItem(id=_mk_id("CON", f"{title}-con1"), title=f"Weakness in: {title}", body="Potential flaw or missing evidence.", fallacies=fallacies),
    ]
    return title, pro_bullets, con_bullets