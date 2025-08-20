from __future__ import annotations
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from jinja2 import Template

class FallacyTool:
    def __init__(self, llm_provider) -> None:
        self.llm = llm_provider
        base = Path(__file__).resolve().parents[1]
        self.tpl_edus = Template((base / "prompts" / "fallacy_edus.md.jinja").read_text(encoding="utf-8"))
        self.tpl_class = Template((base / "prompts" / "fallacy_classify.md.jinja").read_text(encoding="utf-8"))
        self.catalog = json.loads((base / "fallacies" / "catalog.json").read_text(encoding="utf-8"))

    def analyze(self, text: str, families: Optional[List[str]] = None) -> Dict[str, Any]:
        if not self.llm:
            return {"edus": [], "findings": []}
        edus_prompt = self.tpl_edus.render(text=text)
        edus_raw = self.llm.chat_json(edus_prompt, temperature=0.2, max_tokens=300)
        try:
            edus = json.loads(edus_raw).get("edus", [])
        except Exception:
            edus = []
        rules = self.catalog if not families else [r for r in self.catalog if r.get("family") in families]
        short_rules = [
            {"code": r["code"], "name": r["name"], "rule": r["rule"][:140], "example": r["example"]}
            for r in rules
        ]
        cls_prompt = self.tpl_class.render(edus=edus, rules=short_rules)
        cls_raw = self.llm.chat_json(cls_prompt, temperature=0.2, max_tokens=800)
        try:
            return json.loads(cls_raw)
        except Exception:
            return {"edus": []}
