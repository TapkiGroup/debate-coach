from __future__ import annotations
from typing import Dict, Any, List


class PlannerTool:
    def run(self, triage: Dict[str, Any], enable_research_by_default: bool = False) -> Dict[str, Any]:
        intents: List[str] = triage.get("intents", [])
        needs = triage.get("needs", {})
        stance = triage.get("stance", "unclear")

        do_fallacy = bool(needs.get("fallacy_detection") or ("evaluate_argument" in intents))
        do_gen = (
            needs.get("generation", "none") != "none"
            or ("generate_counters" in intents)
            or ("evaluate_argument" in intents)
            or True  
        )
        do_res = bool(needs.get("research") or ("research" in intents) or enable_research_by_default)
        use_heavy = True if needs.get("generation") == "both" and stance in {"mixed", "unclear"} else False

        return {
            "do_fallacy_check": do_fallacy,
            "fallacy_families": None,
            "do_generation": do_gen,
            "use_heavy_model": use_heavy,
            "do_research": do_res,
        }
