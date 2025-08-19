from __future__ import annotations
import os
from openai import OpenAI
from ..core.logger import logger

AIML_BASE_URL = os.getenv("AIML_BASE_URL", "https://api.aimlapi.com/v1")
AIML_API_KEY = os.getenv("AIML_API_KEY")  
DEFAULT_MODEL = os.getenv("AIML_MODEL", "openai/gpt-5-nano-2025-08-07")

class GPT5Client:
    """
    GPT-5 proxy client via AI/ML API (aimlapi.com).
    """

    def __init__(self):
        if not AIML_API_KEY:
            logger.warning("AIML_API_KEY is missing; GPT client will return a stub.")
            self.client = None
        else:
            self.client = OpenAI(base_url=AIML_BASE_URL, api_key=AIML_API_KEY)

    async def chat(self, system: str, user: str, model: str | None = None) -> str:

        if not self.client:
            return (
                "[Coach] (stub) No AIML_API_KEY set. Parsed your message and "
                "would normally call GPT-5 here."
            )
        
        response = self.client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system or ""},
                {"role": "user", "content": user or ""},
            ],
            temperature=0.7,
            top_p=0.7,
            frequency_penalty=1.0,
            max_tokens=500,
        )
        return response.choices[0].message.content or ""

