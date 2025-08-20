def trim(s: str, max_len: int = 1200) -> str:
    s = s.strip()
    return s if len(s) <= max_len else s[:max_len] + "…"
