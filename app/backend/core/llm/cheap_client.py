import requests
from core.config import settings

def _post_chat(model: str, system: str, user: str, temperature: float, max_tokens: int) -> str:
    url = f"{settings.AIMLAPI_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": settings.AIMLAPI_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    r = requests.post(url, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()

def chat(system: str, user: str, temperature: float = 0.2, max_tokens: int = 600) -> str:
    return _post_chat(
        model=settings.CHEAP_MODEL,
        system=system, user=user,
        temperature=temperature, max_tokens=max_tokens
    )
