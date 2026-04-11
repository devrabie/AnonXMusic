# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio
from collections import defaultdict, deque
from typing import Union

from ._dataclass import Media, Track

MediaItem = Union[Media, Track]


class Queue:
    def __init__(self):
        self.queues: dict[int, deque[MediaItem]] = defaultdict(deque)

    async def _save(self, chat_id: int):
        from anony import db
        await db.save_queue(chat_id, list(self.queues[chat_id]))

    async def add(self, chat_id: int, item: MediaItem) -> int:
        """Add an item to the queue and return its position (1-based)."""
        # Avoid duplicates by id
        for existing in self.queues[chat_id]:
            if existing.id == item.id:
                return -2 # Custom code for duplicate

        self.queues[chat_id].append(item)
        await self._save(chat_id)
        return len(self.queues[chat_id]) - 1

    def check_item(self, chat_id: int, item_id: str) -> tuple[int, MediaItem | None]:
        """Check if an item with the given ID exists in the queue."""
        pos, track = next(
            (
                (i, track)
                for i, track in enumerate(list(self.queues[chat_id]))
                if track.id == item_id
            ),
            (-1, None),
        )
        return pos, track

    async def force_add(
        self, chat_id: int, item: MediaItem, remove: int | bool = False
    ) -> None:
        """Replace the currently playing item with a new one."""
        await self.remove_current(chat_id)
        self.queues[chat_id].appendleft(item)
        if remove:
            self.queues[chat_id].rotate(-remove)
            self.queues[chat_id].popleft()
            self.queues[chat_id].rotate(remove)
        await self._save(chat_id)

    def get_current(self, chat_id: int) -> MediaItem | None:
        """Return the currently playing item (first in queue), if any."""
        return self.queues[chat_id][0] if self.queues[chat_id] else None

    async def get_next(self, chat_id: int, check: bool = False) -> MediaItem | None:
        """Remove current item and return the next one, or None if empty."""
        if not self.queues[chat_id]:
            return None
        if check:
            return self.queues[chat_id][1] if len(self.queues[chat_id]) > 1 else None

        from anony import db
        if await db.get_loop(chat_id):
            self.queues[chat_id].rotate(-1)
        else:
            self.queues[chat_id].popleft()

        await self._save(chat_id)
        return self.queues[chat_id][0] if self.queues[chat_id] else None

    async def get_prev(self, chat_id: int) -> MediaItem | None:
        """Rotate the queue backward and return the 'new' current item."""
        if not self.queues[chat_id]:
            return None

        from anony import db
        # We always rotate for prev if loop is on, or even if not, we can rotate back
        # but if loop is off, the head was already popped.
        # However, the user wants to "flip through files from the playlist".
        # So rotating is the correct "flipping" behavior.
        self.queues[chat_id].rotate(1)

        await self._save(chat_id)
        return self.queues[chat_id][0]

    def get_queue(self, chat_id: int) -> list[MediaItem]:
        """Return the full queue including the currently playing item."""
        return list(self.queues[chat_id])

    async def remove_current(self, chat_id: int) -> None:
        """Remove the currently playing item only (if exists)."""
        if self.queues[chat_id]:
            self.queues[chat_id].popleft()
            await self._save(chat_id)

    async def clear(self, chat_id: int) -> None:
        """Clear the entire queue."""
        self.queues[chat_id].clear()
        await self._save(chat_id)
