from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator, Dict, List


class EventHub:
    def __init__(self) -> None:
        self._subscribers: List[asyncio.Queue] = []

    async def publish(self, event: Dict[str, Any]) -> None:
        for queue in list(self._subscribers):
            await queue.put(event)

    async def subscribe(self) -> AsyncGenerator[str, None]:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        try:
            while True:
                event = await queue.get()
                yield f"data: {event}\n\n"
        finally:
            self._subscribers.remove(queue)


event_hub = EventHub()
