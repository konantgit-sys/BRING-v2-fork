"""
Redis bridge: BRING → SkyRift (and any external subscriber)

Publishes world events to Redis channels as JSON.
Any external server (SkyRift MMO, dashboard, etc.) can subscribe
and receive real-time world state updates.

Channel structure:
  bring:npc:spoke     — NPC dialogue events
  bring:npc:moved     — NPC movement
  bring:npc:action    — NPC social interaction / world action
  bring:scene:enter   — Player enters location
  bring:scene:exit    — Player leaves location
  bring:world:pulse   — Periodic world heartbeat (time, weather, etc.)
  bring:story:beat    — Director story beat triggers
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Use redis.asyncio for non-blocking pub/sub in async context
try:
    import redis.asyncio as aioredis
    HAS_AIOREDIS = True
except ImportError:
    aioredis = None
    HAS_AIOREDIS = False


class RedisBridge:
    """
    Async bridge between BRING world engine and external subscribers.

    Usage:
        bridge = RedisBridge("bring")
        await bridge.connect()
        await bridge.npc_spoke(npc_name="Elara", location="Verdant Depths",
                                message="The Inquisition fears what they cannot control.",
                                player="Kaelen Ashvale")
        await bridge.close()
    """

    def __init__(
        self,
        world_id: str = "bring",
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "bring",
    ):
        self.world_id = world_id
        self.redis_url = redis_url
        self.prefix = prefix
        self._client: Optional[aioredis.Redis] = None
        self._connected = False

    async def connect(self) -> bool:
        """Connect to Redis. Returns True on success."""
        if not HAS_AIOREDIS:
            logger.warning("redis.asyncio not available — bridge disabled")
            return False

        try:
            self._client = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=3,
            )
            await self._client.ping()
            self._connected = True
            logger.info(f"RedisBridge connected: {self.redis_url}")
            return True
        except Exception as e:
            logger.warning(f"RedisBridge unavailable: {e}")
            self._connected = False
            return False

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected and self._client is not None

    # ─── Publishing Methods ───────────────────────────────────────

    async def _publish(self, channel: str, event: Dict[str, Any]):
        """Internal: publish a JSON event to a Redis channel."""
        if not self.connected:
            return

        event["world_id"] = self.world_id
        event["timestamp"] = event.get("timestamp", datetime.now().isoformat())

        full_channel = f"{self.prefix}:{channel}"
        payload = json.dumps(event, ensure_ascii=False, default=str)

        try:
            await self._client.publish(full_channel, payload)
            logger.debug(f"PUB {full_channel}: {event.get('type', '?')}")
        except Exception as e:
            logger.warning(f"Redis publish failed ({channel}): {e}")

    async def npc_spoke(
        self,
        npc_name: str,
        npc_uid: str,
        location: str,
        message: str,
        player: str = "",
        mood: str = "neutral",
    ):
        """Publish NPC dialogue event."""
        await self._publish("npc:spoke", {
            "type": "npc_spoke",
            "npc_name": npc_name,
            "npc_uid": npc_uid,
            "location": location,
            "message": message,
            "player": player,
            "mood": mood,
        })

    async def npc_moved(
        self,
        npc_name: str,
        npc_uid: str,
        from_location: str,
        to_location: str,
        reason: str = "",
    ):
        """Publish NPC movement event."""
        await self._publish("npc:moved", {
            "type": "npc_moved",
            "npc_name": npc_name,
            "npc_uid": npc_uid,
            "from": from_location,
            "to": to_location,
            "reason": reason,
        })

    async def npc_action(
        self,
        npc_name: str,
        npc_uid: str,
        location: str,
        action: str,
        target: str = "",
        result: str = "",
    ):
        """Publish NPC action/interaction event (social sim, combat, etc.)."""
        await self._publish("npc:action", {
            "type": "npc_action",
            "npc_name": npc_name,
            "npc_uid": npc_uid,
            "location": location,
            "action": action,
            "target": target,
            "result": result,
        })

    async def scene_enter(
        self,
        character: str,
        location: str,
        description: str = "",
    ):
        """Publish scene entry event."""
        await self._publish("scene:enter", {
            "type": "scene_enter",
            "character": character,
            "location": location,
            "description": description[:500] if description else "",
        })

    async def scene_exit(
        self,
        character: str,
        from_location: str,
        to_location: str,
    ):
        """Publish scene exit event."""
        await self._publish("scene:exit", {
            "type": "scene_exit",
            "character": character,
            "from": from_location,
            "to": to_location,
        })

    async def story_beat(
        self,
        beat_id: str,
        description: str,
        location: str = "",
    ):
        """Publish story beat trigger from the Director."""
        await self._publish("story:beat", {
            "type": "story_beat",
            "beat_id": beat_id,
            "description": description,
            "location": location,
        })

    async def world_pulse(
        self,
        game_time: str,
        active_npcs: int,
        total_events: int,
        locations: List[str] = None,
    ):
        """Publish periodic world heartbeat."""
        await self._publish("world:pulse", {
            "type": "world_pulse",
            "game_time": game_time,
            "active_npcs": active_npcs,
            "total_events": total_events,
            "locations": locations or [],
        })

    # ─── Subscriber (for testing / external clients) ──────────────

    async def subscribe(self, channel_pattern: str = "bring:*"):
        """
        Subscribe to BRING events. Async generator yielding (channel, event_dict).
        Use for testing or building external connectors.
        """
        if not self.connected:
            return

        pubsub = self._client.pubsub()
        await pubsub.psubscribe(channel_pattern)

        try:
            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    try:
                        data = json.loads(message["data"])
                        yield message["channel"], data
                    except json.JSONDecodeError:
                        pass
        finally:
            await pubsub.punsubscribe(channel_pattern)


class BridgeStub:
    """
    No-op bridge — used when Redis is unavailable.
    Same interface as RedisBridge but does nothing.
    """

    def __init__(self, *args, **kwargs):
        pass

    async def connect(self) -> bool:
        return False

    async def close(self):
        pass

    @property
    def connected(self) -> bool:
        return False

    async def npc_spoke(self, *args, **kwargs):
        pass

    async def npc_moved(self, *args, **kwargs):
        pass

    async def npc_action(self, *args, **kwargs):
        pass

    async def scene_enter(self, *args, **kwargs):
        pass

    async def scene_exit(self, *args, **kwargs):
        pass

    async def story_beat(self, *args, **kwargs):
        pass

    async def world_pulse(self, *args, **kwargs):
        pass

    async def subscribe(self, *args, **kwargs):
        return
        yield  # never yields


def create_bridge(
    world_id: str = "bring",
    redis_url: str = "redis://localhost:6379/0",
) -> RedisBridge | BridgeStub:
    """Factory: create bridge with auto-detection of Redis availability."""
    if HAS_AIOREDIS:
        return RedisBridge(world_id=world_id, redis_url=redis_url)
    return BridgeStub()
