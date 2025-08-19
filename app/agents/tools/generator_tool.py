from __future__ import annotations
import json
from typing import Dict, Any
from pathlib import Path
from jinja2 import Template

class GeneratorTool:
    def __init__(self, llm_provider) -> None:
        self.llm = llm_provider
        base = Path(__file__).resolve().parents[1] / "prompts"
        self.tpl_debate = Template((base / "generator_debate.md.jinja").read_text(encoding="utf-8"))
        self.tpl_pitch = Template((base / "generator_pitch.md.jinja").read_text(encoding="utf-8"))

    def run(
        self,
        mode: str,
        message: str,
        triage: Dict[str, Any],
        fallacies: Dict[str, Any] | None,
        sources: list[Dict[str, Any]] | None,
        heavy: bool = False,
        max_tokens: int = 600,
    ) -> Dict[str, Any]:
        if not self.llm:
            return {
                "chat_md": (
                    "## Refined Claim
" \
                    + message + "

## Pros
- Example support.

## Critique
- Example critique.

## Objections
- Example objection.

## Rebuttals
- Example rebuttal.
"
                ),
                "pro_items": [
                    {"title": "Refined claim", "body": message[:160], "tag": "position"},
                    {"title": "Support", "body": "Example support", "tag": "support"},
                ],
                "con_items": [
                    {"title": "Critique", "body": "Example critique", "tag": "critique"},
                    {"title": "Objection", "body": "Example objection", "tag": "objection"},
                ],
            }
        tpl = self.tpl_debate if mode == "debate_coach" else self.tpl_pitch
        prompt = tpl.render(text=message, triage=triage, sources=sources or [])
        content = self.llm.chat_sections_with_json(prompt, temperature=0.4 if mode == "debate_coach" else 0.7, max_tokens=max_tokens)
        pro_items: list[Dict[str, Any]] = []
        con_items: list[Dict[str, Any]] = []
        try:
            jstart = content.rfind("{")
            j = json.loads(content[jstart:]) if jstart != -1 else {}
            pro_items = j.get("pro_items", [])
            con_items = j.get("con_items", [])
        except Exception:
            pass
        return {"chat_md": content, "pro_items": pro_items, "con_items": con_items}
