from src.core.event_bus import EventBus, bus


def test_subscribe_and_publish_calls_handler():
    received = {}

    def handler(payload):
        received.update(payload)

    local_bus = EventBus()
    local_bus.subscribe("evt", handler)
    local_bus.publish("evt", {"x": 42})

    assert received == {"x": 42}


def test_global_bus_works():
    got = {}

    def h(payload):
        got.update(payload)

    bus.subscribe("check", h)
    bus.publish("check", {"ok": True})
    assert got["ok"] is True


def test_handler_error_is_caught(capsys):
    def bad_handler(_):
        raise ValueError("oops")

    b = EventBus()
    b.subscribe("fail", bad_handler)
    # Should not raise
    b.publish("fail", {"a": 1})

    out, err = capsys.readouterr()
    assert "Event handler error" in out