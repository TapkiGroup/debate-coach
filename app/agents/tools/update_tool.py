from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime
import hashlib
import re


class UpdateTool:
    def _hash(self, title: str, body: str) -> str:
        return hashlib.sha256(f"{title}|{body}".encode("utf-8")).hexdigest()[:12]

    def fallacies_to_con_items(self, fallacy_output: Dict[str, Any] | None) -> List[Dict[str, Any]]:
        if not fallacy_output:
            return []
        items: List[Dict[str, Any]] = []
        for edu in fallacy_output.get("edus", []):
            for f in edu.get("fallacies", []):
                title = f.get("code", "fallacy")
                body = f.get("because", "")
                span = f.get("span", "")
                tag = f"fallacy:{title}"
                items.append({
                    "id": f"CON_{self._hash(title, body)}",
                    "title": title,
                    "body": (body + (f" — \u201c{span}\u201d" if span else ""))[:280],
                    "tag": tag,
                })
        return items

    def distill_from_sections(self, chat_md: str) -> Dict[str, List[Dict[str, Any]]]:
        pro, con = [], []
        # naive parse: look for section headers and bullets
        blocks = self._split_sections(chat_md)
        # Map sections to pro/con
        pro_sections = {"refined claim", "pros", "rebuttals", "improvements", "recommendations", "value prop"}
        con_sections = {"critique", "objections", "risks", "weaknesses"}
        for name, content in blocks.items():
            bullets = self._bullets(content)
            if name in pro_sections:
                for b in bullets:
                    pro.append({"id": f"PRO_{self._hash(name, b)}", "title": name.title(), "body": b, "tag": self._pro_tag(name)})
            elif name in con_sections:
                for b in bullets:
                    con.append({"id": f"CON_{self._hash(name, b)}", "title": name.title(), "body": b, "tag": self._con_tag(name)})
        return {"pro": pro, "con": con}

    def _split_sections(self, md: str) -> Dict[str, str]:
        sections: Dict[str, str] = {}
        cur = None
        for line in md.splitlines():
            m = re.match(r"^#+\s+(.*)$", line.strip())
            if m:
                cur = m.group(1).strip().lower()
                sections[cur] = ""
            elif cur is not None:
                sections[cur] += line + "\n"
        return sections

    def _bullets(self, block: str) -> List[str]:
        out = []
        for line in block.splitlines():
            s = line.strip()
            if s.startswith("- ") or s.startswith("• ") or s.startswith("*"):
                s = s.lstrip("-*• ").strip()
                if s:
                    out.append(s)
        # Also extract single-paragraph lines when no bullets are present
        if not out:
            para = block.strip().replace("\n", " ")
            if para:
                out.append(para[:240])
        return out

    def _pro_tag(self, name: str) -> str:
        if "refined" in name or "value prop" in name:
            return "position"
        if "rebuttal" in name:
            return "rebuttal"
        if "improve" in name or "recommend" in name:
            return "improvement"
        return "support"

    def _con_tag(self, name: str) -> str:
        if "objection" in name:
            return "objection"
        if "risk" in name or "weak" in name:
            return "critique"
        return "critique"

    def make_update(self, column: str, items: List[Dict[str, Any]], ts: datetime) -> Dict[str, Any]:
        # dedup by id
        seen = set()
        unique: List[Dict[str, Any]] = []
        for it in items:
            if it.get("id") in seen:
                continue
            seen.add(it.get("id"))
            unique.append(it)
        return {"column": column, "items": unique, "timestamp": ts.isoformat()}


