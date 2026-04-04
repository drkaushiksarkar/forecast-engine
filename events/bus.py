"""Event-driven architecture: publish-subscribe event bus with filtering."""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)

EventHandler = Callable[["Event"], Awaitable[None]]


@dataclass
class Event:
    topic: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source: str = ""
    correlation_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Subscription:
    sub_id: str
    topic_pattern: str
    handler: EventHandler
    filter_fn: Optional[Callable[[Event], bool]] = None
    max_retries: int = 3
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class EventBus:
    """Async pub-sub event bus with topic filtering and retry logic."""

    def __init__(self, max_queue_size: int = 10000) -> None:
        self._subscriptions: dict[str, list[Subscription]] = defaultdict(list)
        self._queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=max_queue_size)
        self._running = False
        self._processed_count = 0
        self._error_count = 0
        self._dead_letter: list[tuple[Event, str]] = []

    def subscribe(
        self,
        topic: str,
        handler: EventHandler,
        filter_fn: Optional[Callable[[Event], bool]] = None,
    ) -> str:
        sub_id = str(uuid.uuid4())[:8]
        sub = Subscription(
            sub_id=sub_id,
            topic_pattern=topic,
            handler=handler,
            filter_fn=filter_fn,
        )
        self._subscriptions[topic].append(sub)
        logger.info("Subscription %s registered for topic '%s'", sub_id, topic)
        return sub_id

    def unsubscribe(self, sub_id: str) -> bool:
        for topic, subs in self._subscriptions.items():
            for i, sub in enumerate(subs):
                if sub.sub_id == sub_id:
                    subs.pop(i)
                    logger.info("Subscription %s removed from topic '%s'", sub_id, topic)
                    return True
        return False

    async def publish(self, event: Event) -> None:
        await self._queue.put(event)

    def publish_sync(self, event: Event) -> None:
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.error("Event queue full, dropping event %s", event.event_id)

    async def _dispatch(self, event: Event) -> None:
        matching_subs = self._subscriptions.get(event.topic, [])
        wildcard_subs = self._subscriptions.get("*", [])
        all_subs = matching_subs + wildcard_subs
        for sub in all_subs:
            if sub.filter_fn and not sub.filter_fn(event):
                continue
            retries = 0
            while retries <= sub.max_retries:
                try:
                    await sub.handler(event)
                    break
                except Exception:
                    retries += 1
                    if retries > sub.max_retries:
                        self._error_count += 1
                        self._dead_letter.append(
                            (event, f"Handler {sub.sub_id} failed after {sub.max_retries} retries")
                        )
                        logger.error(
                            "Event %s dead-lettered after %d retries",
                            event.event_id, sub.max_retries,
                        )
                    else:
                        await asyncio.sleep(0.1 * (2 ** retries))

    async def start(self) -> None:
        self._running = True
        logger.info("Event bus started")
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch(event)
                self._processed_count += 1
            except asyncio.TimeoutError:
                continue

    async def stop(self) -> None:
        self._running = False
        while not self._queue.empty():
            event = self._queue.get_nowait()
            await self._dispatch(event)
            self._processed_count += 1
        logger.info(
            "Event bus stopped. Processed: %d, Errors: %d, Dead letters: %d",
            self._processed_count, self._error_count, len(self._dead_letter),
        )

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "processed": self._processed_count,
            "errors": self._error_count,
            "dead_letters": len(self._dead_letter),
            "queue_size": self._queue.qsize(),
            "subscriptions": sum(len(s) for s in self._subscriptions.values()),
            "topics": list(self._subscriptions.keys()),
        }
