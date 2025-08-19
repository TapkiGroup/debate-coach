# FILE: app/agents/supervisor_agent.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from .tools.triage_tool import TriageTool
from .tools.planner_tool import PlannerTool
from .tools.fallacy_tool import FallacyTool
from .tools.generator_tool import GeneratorTool
from .tools.research_tool import ResearchTool
from .tools.update_tool import UpdateTool


@dataclass
class SupervisorConfig:
    max_tokens_heavy: int = 900
    max_tokens_nano: int = 200
    enable_research_by_default: bool = False


@dataclass
class TurnOutput:
    chat_text: str
    updates: List[Dict[str, Any]] = field(default_factory=list)


class SupervisorAgent:
    """
    Orchestrates tools in a cost-aware pipeline per user turn.
    LLM/Research providers are injected from the backend; no direct env/API usage here.
    """

    def __init__(
        self,
        llm_provider,
        research_provider,
        cfg: Optional[SupervisorConfig] = None,
    ):
        self.cfg = cfg or SupervisorConfig()
        self.triage = TriageTool(llm_provider)
        self.planner = PlannerTool()
        self.fallacy = FallacyTool(llm_provider)
        self.generator = GeneratorTool(llm_provider)
        self.research = ResearchTool(research_provider)
        self.updater = UpdateTool()

    def process_turn(
        self,
        session_id: str,
        mode: str,  # "debate_coach" | "pitch_objection"
        message: str,
        explicit_actions: Optional[List[str]] = None,
    ) -> TurnOutput:
        # 1) TRIAGE (cheap)
        tri = self.triage.run(mode=mode, message=message)

        # Merge explicit actions (from UI) with triage intents
        if explicit_actions:
            tri["intents"] = sorted(list(set(tri.get("intents", []) + explicit_actions)))

        # 2) PLAN (cheap rules)
        plan = self.planner.run(triage=tri, enable_research_by_default=self.cfg.enable_research_by_default)

        # Buckets
        pro_items: List[Dict[str, Any]] = []
        con_items: List[Dict[str, Any]] = []
        sources: List[Dict[str, Any]] = []
        chat_sections_md: str = ""  # what model returns as human-readable sections

        # 3) FALLACY DETECTION (nano) — only if requested by plan
        fallacies = None
        if plan.get("do_fallacy_check"):
            fallacies = self.fallacy.analyze(message, families=plan.get("fallacy_families"))
            con_items.extend(self.updater.fallacies_to_con_items(fallacies))

        # 4) RESEARCH (cheap-mid) — only if requested by plan
        if plan.get("do_research"):
            sources = self.research.run(query=message)

        # 5) GENERATE (nano/heavy) — only if requested by plan
        if plan.get("do_generation"):
            gen = self.generator.run(
                mode=mode,
                message=message,
                triage=tri,
                fallacies=fallacies,
                sources=sources,
                heavy=plan.get("use_heavy_model", False),
                max_tokens=self.cfg.max_tokens_heavy if plan.get("use_heavy_model") else self.cfg.max_tokens_nano,
            )
            chat_sections_md = gen.get("chat_md", "")
            pro_items.extend(gen.get("pro_items", []))
            con_items.extend(gen.get("con_items", []))

        # 6) Always perform a light distillation from chat sections if present
        if chat_sections_md:
            distilled = self.updater.distill_from_sections(chat_sections_md)
            pro_items.extend(distilled.get("pro", []))
            con_items.extend(distilled.get("con", []))

        # 7) Build updates for UI columns
        now = datetime.now(tz=timezone.utc)
        updates = []
        if pro_items:
            updates.append(self.updater.make_update("PRO", pro_items, now))
        if con_items:
            updates.append(self.updater.make_update("CON", con_items, now))
        if sources:
            updates.append(self.updater.make_update("SOURCES", sources, now))

        chat_text = chat_sections_md or "Processed turn. Updated columns accordingly."
        return TurnOutput(chat_text=chat_text, updates=updates)
