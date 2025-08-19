from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any
from jinja2 import Template

class TriageTool:
    def __init__(self, llm_provider) -> None:
        self.llm = llm_provider
        tpl_path = Path(__file__).resolve().parents[1] / "prompts" / "triage.md.jinja"
        self.template = Template(tpl_path.read_text(encoding="utf-8"))

    def run(self, mode: str, message: str) -> Dict[str, Any]:
        if not self.llm:
            return {
                "mode": mode,
                "intents": ["evaluate_argument", "generate_counters"],
                "stance": "mixed",
                "type": "assertion",
                "claims": [{"text": message, "normalized": message.lower(), "confidence": 0.6}],
                "needs": {"fallacy_detection": True, "generation": "both", "research": False},
            }
        prompt = self.template.render(mode=mode, text=message)
        raw = self.llm.chat_json(prompt, temperature=0.2, max_tokens=350)
        try:
            return json.loads(raw)
        except Exception:
            return {
                "mode": mode,
                "intents": ["evaluate_argument"],
                "stance": "unclear",
                "type": "assertion",
                "claims": [{"text": message, "normalized": message.lower(), "confidence": 0.5}],
                "needs": {"fallacy_detection": True, "generation": "pro", "research": False},
            }
