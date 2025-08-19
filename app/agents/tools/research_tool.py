from __future__ import annotations
from typing import List, Dict

class ResearchTool:
    def __init__(self, research_provider) -> None:
        self.research = research_provider

    def run(self, query: str) -> List[Dict]:
        return self.research.search(query)
