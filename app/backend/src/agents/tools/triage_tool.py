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
        raw = self.llm.chat_json(self.template.render(mode=mode, text=message), temperature=0.2, max_tokens=350) if self.llm else "{}"
        try:
            data = json.loads(raw)
        except Exception:
            data = {}

        if not isinstance(data, dict) or not data:
            data = {
                "mode": mode,
                "intents": (["first_impression"] if mode=="pitch_objection" else ["evaluate_argument"]),
                "stance": "unclear",
                "type": "assertion",
                "claims": [{"text": message, "normalized": message.lower(), "confidence": 0.5}],
                "needs": {"fallacy_detection": (mode=="debate_coach"), "generation": "both", "research": False},
            }

        # ---- Agentic audit (no hardcoded patterns) ----
        auditor_tpl = Template((Path(__file__).resolve().parents[1] / "prompts" / "triage_auditor.md.jinja").read_text(encoding="utf-8"))
        audit_raw = self.llm.chat_json(auditor_tpl.render(mode=mode, text=message, triage=data), temperature=0.0, max_tokens=200)
        try:
            audit = json.loads(audit_raw)
        except Exception:
            audit = {}

        if isinstance(audit, dict) and audit:
            # merge agentic corrections
            if audit.get("force_intents"):
                data["intents"] = sorted(list({*data.get("intents", []), *audit["force_intents"]}))
            if audit.get("force_needs"):
                data.setdefault("needs", {}).update(audit["force_needs"])

        return data