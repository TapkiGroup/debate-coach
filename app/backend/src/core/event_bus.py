from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, AsyncIterator
import uuid


@dataclass
class Event:
    """Lightweight event container for in-process pub/sub."""
    topic: str
    type: str
    payload: Dict[str, Any]
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    ts: float = field(default_factory=lambda: datetime.now(tz=timezone.utc).timestamp())


class EventBus:
    """
    Minimal async in-memory event bus with per-topic subscribers.
    - publish(topic, type, payload): broadcast Event to all subscribers.
    - subscribe(topic): async generator yielding Events until consumer stops.
    - subscriber_queue(topic): returns an asyncio.Queue (handy for SSE).
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def publish(self, topic: str, type: str, payload: Dict[str, Any]) -> None:
        evt = Event(topic=topic, type=type, payload=payload)
        async with self._lock:
            queues = list(self._subscribers.get(topic, set()))
        for q in queues:
            try:
                q.put_nowait(evt)
            except asyncio.QueueFull:
                # Drop if consumer is too slow; keep bus non-blocking for demo.
                pass

    async def subscribe(self, topic: str, max_queue: int = 100) -> AsyncIterator[Event]:
        q: asyncio.Queue = asyncio.Queue(maxsize=max_queue)
        async with self._lock:
            self._subscribers.setdefault(topic, set()).add(q)
        try:
            while True:
                evt: Event = await q.get()
                yield evt
        finally:
            await self.unsubscribe_queue(topic, q)

    async def subscriber_queue(self, topic: str, max_queue: int = 100) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=max_queue)
        async with self._lock:
            self._subscribers.setdefault(topic, set()).add(q)
        return q

    async def unsubscribe_queue(self, topic: str, q: asyncio.Queue) -> None:
        async with self._lock:
            subs = self._subscribers.get(topic)
            if subs is None:
                return
            subs.discard(q)
            if not subs:
                self._subscribers.pop(topic, None)


# Module-level singleton (optional)
bus = EventBus()
