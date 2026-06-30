#!/usr/bin/env python3
"""
Test subscriber for Redis bridge.
Run this in a separate terminal to see BRING events in real time.

Usage:
    python3 test_bridge_subscriber.py

Output example:
    [08:02:15] bring:scene:exit — Kaelen Ashvale left The Seven Kingdoms → Cogmarket
    [08:02:16] bring:scene:enter — Kaelen Ashvale entered Cogmarket
    [08:02:20] bring:npc:spoke — Elara Moonshard said "The Inquisition..." to Kaelen Ashvale
"""
import asyncio
import json
from datetime import datetime

import redis.asyncio as aioredis


async def main():
    client = await aioredis.from_url("redis://localhost:6379/0", decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.psubscribe("bring:*")

    print("🔍 Listening for BRING events (bring:*)\n")

    async for message in pubsub.listen():
        if message["type"] != "pmessage":
            continue

        try:
            data = json.loads(message["data"])
        except json.JSONDecodeError:
            continue

        channel = message["channel"]
        event_type = data.get("type", "?")
        ts = datetime.now().strftime("%H:%M:%S")

        if event_type == "scene_exit":
            print(f"[{ts}] 🚪 {channel}: {data['character']} left {data['from']} → {data['to']}")
        elif event_type == "scene_enter":
            desc = data.get("description", "")[:80]
            print(f"[{ts}] 📍 {channel}: {data['character']} entered {data['location']} ({desc}...)")
        elif event_type == "npc_spoke":
            msg = data.get("message", "")[:80]
            print(f"[{ts}] 💬 {channel}: {data['npc_name']} said \"{msg}\" to {data['player']}")
        elif event_type == "story_beat":
            desc = data.get("description", "")[:80]
            print(f"[{ts}] 📖 {channel}: Story beat — {desc}")
        elif event_type == "world_pulse":
            print(f"[{ts}] 🌍 {channel}: World pulse — {data.get('active_npcs')} NPCs, {data.get('total_events')} events")
        else:
            print(f"[{ts}] 📡 {channel}: {event_type} — {json.dumps(data, ensure_ascii=False)[:120]}")


if __name__ == "__main__":
    asyncio.run(main())
