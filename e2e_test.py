"""
WebSocket endpoints — streams telemetry and events to connected clients.
Uses Redis pub/sub so multiple backend instances can scale horizontally.
"""
import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis

from app.core.config import settings

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections per channel."""

    def __init__(self):
        # channel -> set of websockets
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, channel: str, ws: WebSocket):
        await ws.accept()
        self._connections.setdefault(channel, set()).add(ws)
        logger.info(f"WS connected: {channel} ({len(self._connections[channel])} total)")

    def disconnect(self, channel: str, ws: WebSocket):
        if channel in self._connections:
            self._connections[channel].discard(ws)
        logger.info(f"WS disconnected: {channel}")

    async def broadcast(self, channel: str, message: str):
        dead = set()
        for ws in self._connections.get(channel, set()):
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._connections.get(channel, set()).discard(ws)


manager = ConnectionManager()


@router.websocket("/ws/drone/{drone_id}")
async def drone_telemetry_ws(ws: WebSocket, drone_id: str):
    """
    Stream real-time telemetry for a specific drone.
    Subscribes to Redis channel telemetry:{drone_id}
    """
    channel = f"telemetry:{drone_id}"
    await manager.connect(channel, ws)

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    try:
        async def _redis_listener():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await manager.broadcast(channel, message["data"])

        listener_task = asyncio.create_task(_redis_listener())

        # Keep alive + handle client messages
        while True:
            try:
                data = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
                # Echo back any commands for now
                await ws.send_text(json.dumps({"type": "ack", "data": data}))
            except asyncio.TimeoutError:
                await ws.send_text(json.dumps({"type": "ping"}))
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WS error for drone {drone_id}: {e}")
    finally:
        manager.disconnect(channel, ws)
        listener_task.cancel()
        await pubsub.unsubscribe(channel)
        await redis_client.aclose()


@router.websocket("/ws/events")
async def events_ws(ws: WebSocket):
    """
    Stream all system events: detections, mission status changes, etc.
    Subscribes to multiple Redis channels.
    """
    await manager.connect("events", ws)

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis_client.pubsub()
    channels = ["events:missions", "events:detections", "events:system"]
    await pubsub.subscribe(*channels)

    try:
        async def _listener():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = {
                        "channel": message["channel"],
                        "data": json.loads(message["data"]) if isinstance(message["data"], str) else message["data"],
                    }
                    await ws.send_text(json.dumps(payload))

        listener_task = asyncio.create_task(_listener())

        while True:
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                await ws.send_text(json.dumps({"type": "ping"}))
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect("events", ws)
        listener_task.cancel()
        await pubsub.unsubscribe(*channels)
        await redis_client.aclose()


@router.websocket("/ws/fleet")
async def fleet_ws(ws: WebSocket):
    """Broadcast telemetry for all drones — used by Live View dashboard."""
    channel = "fleet"
    await manager.connect(channel, ws)

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis_client.pubsub()
    # Subscribe to pattern: all telemetry channels
    await pubsub.psubscribe("telemetry:*")

    try:
        async def _listener():
            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    drone_id = message["channel"].split(":", 1)[1]
                    raw = message["data"]
                    try:
                        data = json.loads(raw)
                        data["drone_id"] = drone_id
                        await ws.send_text(json.dumps(data))
                    except Exception:
                        pass

        listener_task = asyncio.create_task(_listener())

        while True:
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                await ws.send_text(json.dumps({"type": "ping"}))
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(channel, ws)
        listener_task.cancel()
        await pubsub.punsubscribe("telemetry:*")
        await redis_client.aclose()
