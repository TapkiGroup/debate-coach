from __future__ import annotations
from typing import List, Dict, Any
from openai import OpenAI
import os

AIML_BASE_URL = os.getenv("AIML_BASE_URL")
AIML_API_KEY = os.getenv("AIML_API_KEY")
MODEL_NANO = os.getenv("AIML_MODEL_NANO")
MODEL_HEAVY = os.getenv("AIML_MODEL_HEAVY")

class LLMProvider:

    def __init__(self, client: Optional[OpenAI] = None) -> None:
        self.client = client or (OpenAI(base_url=AIML_BASE_URL, api_key=AIML_API_KEY) if AIML_API_KEY else None)

    # ---------- JSON (classification / planning) ----------
    def chat_json(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 300,
        top_p: float = 0.7,
        frequency_penalty: float = 0.0,
    ) -> str:

        if not self.client:
            return "{}"
        try:
            resp = self.client.chat.completions.create(
                model=model or MODEL_NANO,
                messages=[
                    {"role": "system", "content": "Return ONLY compact JSON. Do not explain. No chain-of-thought."},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or "{}"
        except Exception as e:
            return "{}"

    def chat_json_obj(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 300,
    ) -> Dict[str, Any]:

        raw = self.chat_json(prompt, model=model, temperature=temperature, max_tokens=max_tokens)
        try:
            return json.loads(raw)
        except Exception:
            m = list(re.finditer(r"\{.*\}", raw, flags=re.DOTALL))
            if m:
                try:
                    return json.loads(m[-1].group(0))
                except Exception:
                    pass
            return {}

    # ---------- Sections + trailing JSON (generator) ----------
    def chat_sections_with_json(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 600,
        top_p: float = 0.7,
        frequency_penalty: float = 0.2,
    ) -> str:
        if not self.client:
            return (
                "## Refined Claim\nStub content\n\n"
                "## Pros\n- Example support\n\n"
                "## Critique\n- Example critique\n\n"
                "## Objections\n- Example objection\n\n"
                "## Rebuttals\n- Example rebuttal\n\n"
                '{"pro_items":[{"title":"Refined claim","body":"Stub","tag":"position"}],'
                '"con_items":[{"title":"Critique","body":"Stub","tag":"critique"}]}'
            )
        try:
            resp = self.client.chat.completions.create(
                model=model or MODEL_HEAVY,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Answer in concise MARKDOWN SECTIONS, then append a final COMPACT JSON block. "
                            "Do NOT reveal chain-of-thought."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        except Exception:
            return ""