from __future__ import annotations
import os, re, json
from typing import Any, Dict, Optional
from openai import OpenAI

AIML_BASE_URL = os.getenv("AIML_BASE_URL")
AIML_API_KEY  = os.getenv("AIML_API_KEY")
MODEL_NANO    = os.getenv("AIML_MODEL_NANO")
MODEL_HEAVY   = os.getenv("AIML_MODEL_HEAVY")

FORCE_STUB = os.getenv("LLM_FORCE_STUB", "0").lower() in ("1", "true", "yes")

STUB_SECTIONS = (
    "## Refined Claim\nStub content\n\n"
    "## Pros\n- Example support\n\n"
    "## Critique\n- Example critique\n\n"
    "## Objections\n- Example objection\n\n"
    "## Rebuttals\n- Example rebuttal\n\n"
    '{"pro_items":[{"title":"Refined claim","body":"Stub","tag":"position"}],'
    '"con_items":[{"title":"Critique","body":"Stub","tag":"critique"}]}'
)

class LLMProvider:
    def __init__(self, client: Optional[OpenAI] = None) -> None:
        self.client = None if FORCE_STUB else (client or (OpenAI(base_url=AIML_BASE_URL, api_key=AIML_API_KEY) if AIML_API_KEY else None))
        print(f"[LLM] init: stub={self.is_stub()} base_url={AIML_BASE_URL} model_nano={MODEL_NANO}")

    def is_stub(self) -> bool:
        return self.client is None

    def _coerce_str(self, x: object) -> str:
        return "" if x is None else (x if isinstance(x, str) else str(x))

    def chat_json(self, prompt: str, *, model: Optional[str] = None,
                temperature: float = 0.2, max_tokens: int = 300) -> str:
        if self.is_stub():
            print("[LLM] chat_json: STUB")
            return "{}"
        try:
            payload = {
                "model": model or MODEL_NANO,
                "messages": [
                    {"role": "system", "content": "Return ONLY compact JSON. Do not explain. No chain-of-thought."},
                    {"role": "user",   "content": self._coerce_str(prompt)},
                ],
                "temperature": float(temperature),
                "top_p": 0.7,
                "max_tokens": int(max_tokens),
            }
            # sanity-serialize to guarantee no Ellipsis sneaks in
            json.dumps(payload)
            resp = self.client.chat.completions.create(**payload)
            return resp.choices[0].message.content or "{}"
        except Exception as e:
            print(f"[LLM] chat_json EXCEPTION -> stub: {e}")
            return "{}"

    def chat_sections_with_json(self, prompt: str, *, model: Optional[str] = None,
                                temperature: float = 0.4, max_tokens: int = 600) -> str:
        if self.is_stub():
            print("[LLM] chat_sections_with_json: STUB")
            return STUB_SECTIONS
        try:
            payload = {
                "model": model or MODEL_NANO,
                "messages": [
                    {"role": "system", "content": "Answer in concise MARKDOWN SECTIONS, then append a final COMPACT JSON block. No chain-of-thought."},
                    {"role": "user",   "content": self._coerce_str(prompt)},
                ],
                "temperature": float(temperature),
                "top_p": 0.7,
                "max_tokens": int(max_tokens),
            }
            json.dumps(payload)
            resp = self.client.chat.completions.create(**payload)
            return resp.choices[0].message.content or STUB_SECTIONS
        except Exception as e:
            print(f"[LLM] chat_sections_with_json EXCEPTION -> stub: {e}")
            return STUB_SECTIONS

