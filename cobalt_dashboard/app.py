#!/usr/bin/env python3
"""
Cobalt Dashboard — BRING World Manager
FastAPI backend serving world state + SSE event stream from Redis.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --------------- Config ---------------
WORLD_DB = Path("/home/agent/data/projects/BRING-v2-fork/world_db")
ENTITIES_PATH = WORLD_DB / "entities.json"
TIMELINE_PATH = WORLD_DB / "timeline.jsonl"
CLOCK_PATH = WORLD_DB / "world_clock.json"
FRAME_PATH = WORLD_DB / "world_frame.json"
REDIS_URL = "redis://localhost:6379/0"

# --------------- Logging ---------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cobalt")

# --------------- App ---------------
app = FastAPI(title="Cobalt Dashboard", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# --------------- Data Models ---------------
class WorldStats(BaseModel):
    total_entities: int
    characters: int
    factions: int
    locations: int
    artifacts: int
    events: int
    total_timeline: int
    world_name: str
    game_time: str
    clock_speed: float


# --------------- Data Readers ---------------
def _load_json(path: Path) -> dict | list:
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _count_entities() -> dict:
    data = _load_json(ENTITIES_PATH)
    if not data:
        return {}
    
    items = data if isinstance(data, list) else list(data.values())
    counts = {"Character": 0, "Faction": 0, "Location": 0, "Item": 0, "Event": 0, "Race": 0, "WorldRule": 0}
    
    for node in items:
        if isinstance(node, dict):
            entity_type = node.get("entity_type", "Other")
            counts[entity_type] = counts.get(entity_type, 0) + 1
    
    counts["total"] = sum(counts.values())
    return counts


def _read_timeline(limit: int = 50) -> list:
    entries = []
    path = TIMELINE_PATH
    if not path.exists():
        return entries
    
    with open(path, "r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    
    return entries[-limit:]


def _read_clock() -> dict:
    clock = _load_json(CLOCK_PATH)
    return clock if isinstance(clock, dict) else {}


# --------------- Routes ---------------
@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path(__file__).parent / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text())
    return HTMLResponse("<h1>Cobalt Dashboard</h1><p>index.html not found</p>")


@app.get("/api/stats")
async def api_stats():
    """World statistics."""
    counts = _count_entities()
    clock = _read_clock()
    frame = _load_json(FRAME_PATH) if FRAME_PATH.exists() else {}
    if isinstance(frame, dict):
        world_name = frame.get("world_name", "Unknown")
    else:
        world_name = "Unknown"
    
    return {
        "total_entities": counts.get("total", 0),
        "characters": counts.get("Character", 0),
        "factions": counts.get("Faction", 0),
        "locations": counts.get("Location", 0),
        "items": counts.get("Item", 0),
        "events": counts.get("Event", 0),
        "races": counts.get("Race", 0),
        "world_rules": counts.get("WorldRule", 0),
        "world_name": world_name,
        "game_time": clock.get("current_time", datetime.now().isoformat()),
        "clock_speed": clock.get("speed", 1.0),
    }


@app.get("/api/entities")
async def api_entities():
    """All entities with classification."""
    data = _load_json(ENTITIES_PATH)
    if not data:
        return {"entities": [], "count": 0}
    
    items = data if isinstance(data, list) else list(data.values())
    entities = []
    
    for node in items:
        if isinstance(node, dict):
            profile = node.get("profile", {})
            l1 = profile.get("l1", {})
            l2 = profile.get("l2", {})
            entities.append({
                "uid": node.get("uid", ""),
                "name": node.get("name", "Unknown"),
                "type": node.get("entity_type", "unknown"),
                "location": l2.get("location", l1.get("location", "unknown")),
                "description": l2.get("description", l1.get("summary", ""))[:200],
            })
    
    return {"entities": entities, "count": len(entities)}


@app.get("/api/timeline")
async def api_timeline(limit: int = 100, group: str = None):
    """Timeline events."""
    entries = _read_timeline(limit)
    if group:
        entries = [e for e in entries if e.get("group") == group]
    return {"events": entries, "count": len(entries)}


@app.get("/api/clock")
async def api_clock():
    """World clock state."""
    return _read_clock()


@app.get("/api/redis-status")
async def api_redis_status():
    """Check Redis connectivity."""
    try:
        import redis.asyncio as aioredis
        client = await aioredis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        await client.ping()
        await client.close()
        return {"connected": True, "url": REDIS_URL}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@app.get("/api/events/stream")
async def api_events_stream():
    """SSE stream of live Redis events."""
    async def event_stream():
        try:
            import redis.asyncio as aioredis
            client = await aioredis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=3)
            await client.ping()
            pubsub = client.pubsub()
            await pubsub.psubscribe("bring:*")
            
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Redis connected'})}\n\n"
            
            async for message in pubsub.listen():
                if message["type"] != "pmessage":
                    continue
                try:
                    data = json.loads(message["data"])
                    channel = message["channel"].decode() if isinstance(message["channel"], bytes) else message["channel"]
                    yield f"data: {json.dumps({'channel': channel, 'event': data})}\n\n"
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Redis unavailable: {e}'})}\n\n"
            yield f"data: {json.dumps({'type': 'disconnected', 'message': 'Retry in 5s'})}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/health")
async def api_health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "cobalt-dashboard",
    }


# --------------- Entry Point ---------------
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Cobalt Dashboard on port 9901")
    uvicorn.run(app, host="0.0.0.0", port=9901, log_level="info")
