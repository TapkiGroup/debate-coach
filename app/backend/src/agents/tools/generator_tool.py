from __future__ import annotations
import json, re
from typing import Dict, Any
from pathlib import Path
from jinja2 import Template

import os

MODEL_NANO    = os.getenv("AIML_MODEL_NANO")
MODEL_HEAVY   = os.getenv("AIML_MODEL_HEAVY")

class GeneratorTool:
    def __init__(self, llm_provider) -> None:
        self.llm = llm_provider
        base = Path(__file__).resolve().parents[1] / "prompts"
        self.tpl_debate = Template((base / "generator_debate.md.jinja").read_text(encoding="utf-8"))
        self.tpl_pitch  = Template((base / "generator_pitch.md.jinja").read_text(encoding="utf-8"))

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
        # offline stub
        if not self.llm:
            return {
                "chat_md": (
                    "## Refined Claim\n" + message
                    + "\n\n## Pros\n- Example support.\n\n## Critique\n- Example critique.\n\n"
                      "## Objections\n- Example objection.\n\n## Rebuttals\n- Example rebuttal.\n"
                ),
                "pro_items": [
                    {"title":"Refined claim","body":message[:160],"tag":"position"},
                    {"title":"Support","body":"Example support","tag":"support"},
                ],
                "con_items": [
                    {"title":"Critique","body":"Example critique","tag":"critique"},
                    {"title":"Objection","body":"Example objection","tag":"objection"},
                ],
            }

        tpl = self.tpl_debate if mode == "debate_coach" else self.tpl_pitch
        prompt = tpl.render(text=message, triage=triage, sources=sources or [])

        # Heavy OR nano
        model = MODEL_HEAVY if heavy else MODEL_NANO
        content = self.llm.chat_sections_with_json(
            prompt,
            model=model,
            temperature=0.4 if mode == "debate_coach" else 0.7,
            max_tokens=max_tokens,
        )

        pro_items: list[Dict[str, Any]] = []
        con_items: list[Dict[str, Any]] = []
        blob = None
        m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```[\s]*$", content)
        if m:
            blob = m.group(1)
        else:
            mm = list(re.finditer(r"\{[\s\S]*\}", content))
            if mm:
                blob = mm[-1].group(0)
        if blob:
            try:
                j = json.loads(blob)
                pro_items = j.get("pro_items", []) or []
                con_items = j.get("con_items", []) or []
            except Exception:
                pass

        return {"chat_md": content, "pro_items": pro_items, "con_items": con_items}