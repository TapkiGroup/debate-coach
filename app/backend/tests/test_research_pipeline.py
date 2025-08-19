import asyncio
from src.services.research.research_pipeline import run_research

def test_run_research_returns_items():
    items = asyncio.run(run_research("universal basic income"))
    assert isinstance(items, list)
    assert len(items) > 0
    sample = items[0]
    assert {"id","title","url","note","relation"}.issubset(sample.model_dump().keys())
