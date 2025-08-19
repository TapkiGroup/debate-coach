"""
Tests for the synchronous EventBus stub currently present in src/core/event_bus.py
"""
from src.core.event_bus import EventBus


def test_event_bus_subscribe_and_publish():
    bus = EventBus()
    captured = {}

    def handler(payload):
        captured["payload"] = payload

    bus.subscribe("column_update", handler)
    bus.publish("column_update", {"column": "PRO"})
    assert captured["payload"]["column"] == "PRO"
