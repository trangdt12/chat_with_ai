"""Registry các câu trả lời đang stream, dùng cho nút Dừng.

Bản thử nghiệm chạy một tiến trình `api` (uvicorn --workers 1) nên registry trong bộ nhớ là đủ.
Chạy nhiều worker thì chuyển sang PostgreSQL LISTEN/NOTIFY (Blueprint DD-08).
"""

import asyncio
import uuid
from dataclasses import dataclass, field


@dataclass
class ActiveStream:
    user_id: uuid.UUID
    cancel: asyncio.Event = field(default_factory=asyncio.Event)


class StreamRegistry:
    def __init__(self) -> None:
        self._streams: dict[uuid.UUID, ActiveStream] = {}

    def add(self, message_id: uuid.UUID, user_id: uuid.UUID) -> asyncio.Event:
        stream = ActiveStream(user_id)
        self._streams[message_id] = stream
        return stream.cancel

    def remove(self, message_id: uuid.UUID) -> None:
        self._streams.pop(message_id, None)

    def stop(self, message_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Idempotent: không tìm thấy (đã kết thúc) hoặc không phải chủ thì bỏ qua, không lộ thông tin."""
        stream = self._streams.get(message_id)
        if stream and stream.user_id == user_id:
            stream.cancel.set()


registry = StreamRegistry()
