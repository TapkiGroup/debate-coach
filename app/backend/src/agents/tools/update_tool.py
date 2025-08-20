# FILE: app/backend/src/agents/tools/update_tool.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import hashlib
import re
from pathlib import Path
from jinja2 import Template

class UpdateTool:
    """
    Собирает короткие выжимки для колонок PRO/CON из:
    - последнего сообщения пользователя (user_text),
    - секционных ответов ассистента (chat_md),
    - найденных фалласи (опционально).

    Делает 1 вызов LLM для суммаризации и оценки силы PRO.
    """

    def __init__(self, llm_provider=None) -> None:
        self.llm = llm_provider

        self.tpl = Template(
            (
                "You are a debate summarizer. Read USER and ASSISTANT content.\n"
                "Return ONLY JSON with keys:\n"
                "{\"pro_summary\": str, \"pro_strength\": int, \"pro_impression\": str, \"con_summary\": str}\n"
                "Rules:\n"
                "- pro_summary: one concise paragraph (<= 280 chars) that captures the user's stance and assistant's supportive content (Refined Claim/Pros/Rebuttals).\n"
                "- con_summary: one concise paragraph (<= 280 chars) for critique/counterpoints (Critique/Objections) and any fallacies found.\n"
                "- pro_strength: 0..100, overall persuasive strength (clarity, evidence, plausibility).\n"
                "- pro_impression: 2-6 words (e.g., \"clear but under-evidenced\").\n"
                "- If no content for a side, return empty string for the summary and 0 for strength.\n\n"
                "USER:\n\"\"\"\n{{ user_text }}\n\"\"\"\n\n"
                "ASSISTANT_MD_SECTIONS:\n\"\"\"\n{{ chat_md }}\n\"\"\"\n\n"
                "FALLACIES (optional, short):\n{{ fallacy_hint }}\n"
            )
        )

    # ---------- public API ----------

    def summarize_and_make_updates(
        self,
        *,
        mode: str,
        user_text: str,
        chat_md: str,
        fallacies: Optional[Dict[str, Any]],
        ts: datetime,
    ) -> List[Dict[str, Any]]:

        pro_src, con_src = self._extract_sources(user_text, chat_md, fallacies)
        pro_text, pro_strength, pro_impr, con_text = self._summarize_with_llm(
            user_text=user_text,
            chat_md=chat_md,
            fallacy_hint=self._fallacy_hint(fallacies),
        )

        updates: List[Dict[str, Any]] = []
        if pro_text:
            body = f"{pro_text} — Strength: {pro_strength}/100; Impression: {pro_impr}".strip()
            updates.append(self._single_text_update("PRO", body, ts))
        if con_text:
            updates.append(self._single_text_update("CON", con_text, ts))
        # Fallback
        if not updates and (pro_src or con_src):
            if pro_src:
                body = (pro_src[:260] + " — Strength: 60/100; Impression: baseline")[:320]
                updates.append(self._single_text_update("PRO", body, ts))
            if con_src:
                updates.append(self._single_text_update("CON", con_src[:320], ts))
        return updates

    # ---------- helpers ----------

    def _single_text_update(self, column: str, body: str, ts: datetime) -> Dict[str, Any]:
        _id = f"{column}_{self._hash('Summary', body)}"
        item = {"id": _id, "title": "Summary", "body": body, "tag": "summary"}
        return {"column": column, "items": [item], "timestamp": ts.isoformat()}

    def _hash(self, title: str, body: str) -> str:
        import hashlib
        return hashlib.sha256(f"{title}|{body}".encode("utf-8")).hexdigest()[:12]

    def _extract_sources(
        self, user_text: str, chat_md: str, fallacies: Optional[Dict[str, Any]]
    ) -> Tuple[str, str]:

        blocks = self._split_sections(chat_md)
        # PRO 
        pro_sections = ["refined claim", "refined value prop", "pros", "rebuttals", "improvements", "recommendations", "value prop"]
        pro_frag = []
        if user_text:
            pro_frag.append(user_text.strip())
        for name in pro_sections:
            if name in blocks:
                pro_frag.extend(self._bullets(blocks[name]))
        # CON 
        con_sections = ["critique", "objections", "risks", "weaknesses"]
        con_frag = []
        for name in con_sections:
            if name in blocks:
                con_frag.extend(self._bullets(blocks[name]))
        # fallacies кратко
        if fallacies:
            hints = []
            for edu in fallacies.get("edus", []):
                for f in edu.get("fallacies", []):
                    code = str(f.get("code", "fallacy"))
                    hints.append(code.replace("_", " "))
            if hints:
                con_frag.append("fallacies: " + ", ".join(sorted(set(hints)))[:180])
        return ("; ".join(pro_frag)[:600], "; ".join(con_frag)[:600])

    def _fallacy_hint(self, fallacies: Optional[Dict[str, Any]]) -> str:
        if not fallacies:
            return ""
        out = []
        for edu in fallacies.get("edus", []):
            for f in edu.get("fallacies", []):
                code = str(f.get("code", "fallacy"))
                span = str(f.get("span", ""))[:80]
                out.append(f"{code}: \"{span}\"")
        return "; ".join(out)[:300]

    def _split_sections(self, md: str) -> Dict[str, str]:
        sections: Dict[str, str] = {}
        cur = None
        for line in (md or "").splitlines():
            m = re.match(r"^#+\s+(.*)$", line.strip())
            if m:
                cur = m.group(1).strip().lower()
                sections[cur] = ""
            elif cur is not None:
                sections[cur] += line + "\n"
        return sections

    def _bullets(self, block: str) -> List[str]:
        out = []
        for line in (block or "").splitlines():
            s = line.strip()
            if s.startswith("- ") or s.startswith("• ") or s.startswith("*"):
                s = s.lstrip("-*• ").strip()
                if s:
                    out.append(s)
        if not out:
            para = (block or "").strip().replace("\n", " ")
            if para:
                out.append(para[:240])
        return out

    def _summarize_with_llm(
        self,
        *,
        user_text: str,
        chat_md: str,
        fallacy_hint: str,
    ) -> Tuple[str, int, str, str]:
        """1 LLM-call"""
        prompt = self.tpl.render(user_text=user_text, chat_md=chat_md, fallacy_hint=fallacy_hint)
        if not self.llm:
            # offline fallback
            pro_text = (user_text or "")[:240] or "Support summary"
            con_text = "Critique summary"
            return pro_text, 60, "baseline", con_text

        raw = self.llm.chat_json(prompt, temperature=0.2, max_tokens=320)
        try:
            import json
            data = json.loads(raw or "{}")
        except Exception:
            data = {}
        pro_text = str(data.get("pro_summary", "") or "").strip()
        con_text = str(data.get("con_summary", "") or "").strip()
        try:
            pro_strength = int(data.get("pro_strength", 0))
        except Exception:
            pro_strength = 0
        pro_impr = str(data.get("pro_impression", "") or "").strip() or "—"
        return pro_text, max(0, min(100, pro_strength)), pro_impr, con_text
