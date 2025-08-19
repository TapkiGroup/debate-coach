from src.services.research_provider import ResearchProvider

def test_research_provider_returns_items():
    items = ResearchProvider().search("universal basic income")
    assert isinstance(items, list)
    if items:  
        keys = set(items[0].keys())
        assert {"id","title","url","note","relation"} <= keys