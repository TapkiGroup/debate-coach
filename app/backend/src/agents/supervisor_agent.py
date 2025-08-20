# FILE: app/agents/supervisor_agent.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import re

from .tools.triage_tool import TriageTool
from .tools.planner_tool import PlannerTool
from .tools.fallacy_tool import FallacyTool
from .tools.generator_tool import GeneratorTool
from .tools.research_tool import ResearchTool
from .tools.update_tool import UpdateTool


@dataclass
class SupervisorConfig:
    max_tokens_heavy: int = 300
    max_tokens_nano: int = 100
    enable_research_by_default: bool = False
    trace: bool = True


@dataclass
class TurnOutput:
    chat_text: str
    updates: List[Dict[str, Any]] = field(default_factory=list)


class SupervisorAgent:
    def __init__(self, llm_provider, research_provider, cfg: Optional[SupervisorConfig] = None):
        self.cfg = cfg or SupervisorConfig()
        self.triage = TriageTool(llm_provider)
        self.planner = PlannerTool()
        self.fallacy = FallacyTool(llm_provider)
        self.generator = GeneratorTool(llm_provider)
        self.research = ResearchTool(research_provider)
        self.updater = UpdateTool(llm_provider)

    def process_turn(
        self,
        session_id: str,
        mode: str, 
        message: str,
        explicit_actions: Optional[List[str]] = None,
        ) -> TurnOutput:

        if self.cfg.trace: print("[SUP] step=triage:start")
        tri = self.triage.run(mode=mode, message=message)
        if self.cfg.trace: print(f"[SUP] triage -> intents={tri.get('intents')} needs={tri.get('needs')} stance={tri.get('stance')}")

        if explicit_actions:
            tri["intents"] = sorted(list(set(tri.get("intents", []) + explicit_actions)))
            if self.cfg.trace: print(f"[SUP] explicit_actions merged -> intents={tri['intents']}")

        plan = self.planner.run(triage=tri, enable_research_by_default=self.cfg.enable_research_by_default)
        if self.cfg.trace: print(f"[SUP] plan -> {plan}")

        pro_items, con_items, sources = [], [], []
        chat_sections_md = ""

        # fallacy
        if plan.get("do_fallacy_check"):
            if self.cfg.trace: print("[SUP] step=fallacy:start")
            fallacies = self.fallacy.analyze(message, families=plan.get("fallacy_families"))
            fi = self.updater._fallacy_hint(fallacies)
            con_items.extend(fi)
            if self.cfg.trace: print(f"[SUP] fallacy -> con_items+={len(fi)}")
        else:
            fallacies = None

        # research
        if plan.get("do_research"):
            if self.cfg.trace: print("[SUP] step=research:start")
            sources = self.research.run(query=message)
            if self.cfg.trace: print(f"[SUP] research -> sources={len(sources)}")

        # generate
        if plan.get("do_generation"):
            if self.cfg.trace: print("[SUP] step=generator:start")
            gen = self.generator.run(
                mode=mode, message=message, triage=tri, fallacies=fallacies, sources=sources,
                heavy=plan.get("use_heavy_model", False),
                max_tokens=self.cfg.max_tokens_heavy if plan.get("use_heavy_model") else self.cfg.max_tokens_nano,
            )
            chat_sections_md = gen.get("chat_md", "")
            pro_items.extend(gen.get("pro_items", []))
            con_items.extend(gen.get("con_items", []))
            if self.cfg.trace: print(f"[SUP] generator -> sections={'yes' if chat_sections_md else 'no'} pro={len(pro_items)} con={len(con_items)}")

        # Fallback generation (на всякий случай)
        if not pro_items and not con_items and not chat_sections_md:
            if self.cfg.trace: print("[SUP] fallback=generator")
            gen = self.generator.run(
                mode=mode, message=message, triage=tri, fallacies=None, sources=[], heavy=False,
                max_tokens=self.cfg.max_tokens_nano,
            )
            chat_sections_md = gen.get("chat_md", "")
            pro_items.extend(gen.get("pro_items", []))
            con_items.extend(gen.get("con_items", []))
            if self.cfg.trace: print(f"[SUP] fallback -> sections={'yes' if chat_sections_md else 'no'} pro={len(pro_items)} con={len(con_items)}")

        # Distill sections
        now = datetime.now(tz=timezone.utc)
        updates = self.updater.summarize_and_make_updates(
            mode=mode,
            user_text=message,
            chat_md=chat_sections_md,
            fallacies=fallacies,
            ts=now,
        )

        # 7) Build updates for UI columns
        now = datetime.now(tz=timezone.utc)
        chat_text = chat_sections_md or "Summarized columns."
        
        return TurnOutput(chat_text=chat_text, updates=updates)
