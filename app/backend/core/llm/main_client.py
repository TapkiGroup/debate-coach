import os
from openai import OpenAI
from core.config import settings

client = OpenAI(
    base_url=os.getenv("AIML_BASE_URL"),
    api_key=os.getenv("AIML_API_KEY"),
)

def chat(system: str, user: str, temperature: float = 0.7, max_tokens: int = 1600) -> str:
    response = client.chat.completions.create(
        model=settings.MAIN_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content
