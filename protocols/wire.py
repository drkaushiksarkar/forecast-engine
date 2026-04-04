"""Network protocol handlers for inter-service communication."""
from __future__ import annotations

import asyncio
import json
import logging
import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)

MAGIC_BYTES = b"\x53\x41\x47\x45"
HEADER_SIZE = 16
MAX_MESSAGE_SIZE = 64 * 1024 * 1024


class MessageType(IntEnum):
    HEARTBEAT = 0
    REQUEST = 1
    RESPONSE = 2
    ERROR = 3
    STREAM_START = 4
    STREAM_CHUNK = 5
    STREAM_END = 6
    AUTH = 7


@dataclass
class MessageHeader:
    magic: bytes = MAGIC_BYTES
    version: int = 1
    msg_type: MessageType = MessageType.REQUEST
    payload_size: int = 0
    sequence_id: int = 0

    def pack(self) -> bytes:
        return struct.pack(
            "!4sBBIH2x",
            self.magic,
            self.version,
            self.msg_type,
            self.payload_size,
            self.sequence_id,
        )

    @classmethod
    def unpack(cls, data: bytes) -> "MessageHeader":
        if len(data) < HEADER_SIZE:
            raise ValueError(f"Header too short: {len(data)} < {HEADER_SIZE}")
        magic, version, msg_type, size, seq = struct.unpack("!4sBBIH2x", data[:HEADER_SIZE])
        if magic != MAGIC_BYTES:
            raise ValueError(f"Invalid magic bytes: {magic!r}")
        return cls(
            magic=magic,
            version=version,
            msg_type=MessageType(msg_type),
            payload_size=size,
            sequence_id=seq,
        )


@dataclass
class Message:
    header: MessageHeader
    payload: dict[str, Any] = field(default_factory=dict)

    def serialize(self) -> bytes:
        payload_bytes = json.dumps(self.payload).encode("utf-8")
        self.header.payload_size = len(payload_bytes)
        return self.header.pack() + payload_bytes

    @classmethod
    def deserialize(cls, data: bytes) -> "Message":
        header = MessageHeader.unpack(data[:HEADER_SIZE])
        payload_bytes = data[HEADER_SIZE: HEADER_SIZE + header.payload_size]
        payload = json.loads(payload_bytes) if payload_bytes else {}
        return cls(header=header, payload=payload)


MessageHandler = Callable[[Message], Awaitable[Optional[Message]]]


class ProtocolServer:
    """Async TCP server implementing the SAGE wire protocol."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self._handlers: dict[MessageType, MessageHandler] = {}
        self._server: Optional[asyncio.AbstractServer] = None
        self._sequence = 0
        self._connections: set[asyncio.Task] = set()

    def on(self, msg_type: MessageType) -> Callable:
        def decorator(func: MessageHandler) -> MessageHandler:
            self._handlers[msg_type] = func
            return func
        return decorator

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        peer = writer.get_extra_info("peername")
        logger.info("Connection from %s", peer)
        try:
            while True:
                header_data = await reader.readexactly(HEADER_SIZE)
                header = MessageHeader.unpack(header_data)
                if header.payload_size > MAX_MESSAGE_SIZE:
                    logger.error("Message too large: %d bytes", header.payload_size)
                    break
                payload_data = await reader.readexactly(header.payload_size)
                msg = Message.deserialize(header_data + payload_data)
                handler = self._handlers.get(msg.header.msg_type)
                if handler is None:
                    logger.warning("No handler for message type %s", msg.header.msg_type)
                    continue
                response = await handler(msg)
                if response is not None:
                    writer.write(response.serialize())
                    await writer.drain()
        except asyncio.IncompleteReadError:
            logger.info("Connection closed by %s", peer)
        except Exception:
            logger.exception("Error handling connection from %s", peer)
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_connection, self.host, self.port
        )
        logger.info("Protocol server listening on %s:%d", self.host, self.port)
        async with self._server:
            await self._server.serve_forever()

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            for task in self._connections:
                task.cancel()
            logger.info("Protocol server stopped")


class ProtocolClient:
    """Async TCP client for the SAGE wire protocol."""

    def __init__(self, host: str = "localhost", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._sequence = 0

    async def connect(self) -> None:
        self._reader, self._writer = await asyncio.open_connection(self.host, self.port)

    async def send(self, msg_type: MessageType, payload: dict[str, Any]) -> Optional[Message]:
        if self._writer is None or self._reader is None:
            raise RuntimeError("Not connected")
        self._sequence += 1
        msg = Message(
            header=MessageHeader(msg_type=msg_type, sequence_id=self._sequence),
            payload=payload,
        )
        self._writer.write(msg.serialize())
        await self._writer.drain()
        header_data = await self._reader.readexactly(HEADER_SIZE)
        header = MessageHeader.unpack(header_data)
        payload_data = await self._reader.readexactly(header.payload_size)
        return Message.deserialize(header_data + payload_data)

    async def close(self) -> None:
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
