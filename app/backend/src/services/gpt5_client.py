from __future__ import annotations
from openai import AsyncOpenAI
from .prompt_templates import SYSTEM_CORE
from ..core.settings import settings
from ..core.logger import logger

class GPT5Client:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def chat(self, system: str, user: str) -> str:
        """
        Sends a chat completion request to OpenAI.
        Returns assistant text. Falls back to a deterministic stub if no API key.
        """
        if not self.client:
            logger.warning("OPENAI_API_KEY missing. Using dummy GPT-5 response.")
            return (
                "[Coach] OPENAI_API_KEY missing"
            )

        try:
            # Build standard chat messages
            messages = [
                {"role": "system", "content": system or SYSTEM_CORE},
                {"role": "user", "content": user},
            ]

            # Call Chat Completions API (async)
            resp = await self.client.responses.create(
                model=DEFAULT_MODEL,
                input=[
                    {"role": "system", "content": system or SYSTEM_CORE},
                    {"role": "user", "content": user},
                ],
            )
            return getattr(resp, "output_text", "") or ""
            
        except Exception as e:
            logger.exception("OpenAI chat call failed: %s", e)
            # graceful fallback so the app keeps working in demo
            return (
                "[Coach] The live model call failed."
            )

