from pydantic import BaseModel
import os


class Settings(BaseModel):
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    tavily_api_key: str | None = os.getenv("TAVILY_API_KEY")
    port: int = int(os.getenv("PORT", "8000"))


settings = Settings()