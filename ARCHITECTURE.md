# BRING-v2 Architecture

## Overview

BRING-v2-fork is an AI-powered world simulation engine. It procedurally generates a living fantasy world (Aethra) with NPCs, factions, locations, items, and narrative events — all driven by LLM inference via Mistral API.

## System Diagram

```
┌──────────────────────────────────────────────────────────┐
│                   BRING-v2-fork                           │
│                                                          │
│  ┌─────────────┐   ┌──────────────┐   ┌───────────────┐ │
│  │ World       │   │ Narrative    │   │ Roleplay      │ │
│  │ Builder     │──▶│ Engine       │──▶│ Engine        │ │
│  │ (entities)  │   │ (story arc)  │   │ (interaction) │ │
│  └─────────────┘   └──────────────┘   └───────────────┘ │
│         │                 │                   │          │
│         ▼                 ▼                   ▼          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Entity Store (JSON)                  │   │
│  │  32 entities: 5 chars, 5 factions, 6 locations,   │   │
│  │  4 items, 4 events, 4 races, 4 world rules        │   │
│  └──────────────────────────────────────────────────┘   │
│         │                 │                   │          │
│         ▼                 ▼                   ▼          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Mistral API (small-latest)            │   │
│  │  Text generation + Embeddings (384-dim)           │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                              │
│                          ▼                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Redis Bridge (pub/sub)                    │   │
│  │  brings:* channels → external subscribers         │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                              │
└──────────────────────────┼──────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│              Cobalt Dashboard (FastAPI)                   │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Stats    │  │ Map      │  │ Timeline │  │ Live    │ │
│  │ API      │  │ (D3.js)  │  │ (JSONL)  │  │ (SSE)   │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└──────────────────────────────────────────────────────────┘
```

## Component Details

### World Builder (`world_builder/`)
- **entity_store.py** — CRUD for all world entities
- Generates the world from YAML/config definitions
- Populates initial entities (races, factions, locations, characters)

### Narrative Engine (`world_narrative/`)
- **director.py** — Scene Director: orchestrates story beats
- **story_engine.py** — Drives the main plot arc
- **chronicler.py** — Logs all events to timeline.jsonl
- **world_clock.py** — In-game time management with scheduled events
- **birth.py** — Creates world genesis narrative
- **story_planner.py** — Plans narrative arcs
- **villain_manager.py** — Manages antagonist NPCs
- **memory_optimized.py** — Efficient context management

### Roleplay Engine (`world_engine/`)
- **roleplay_engine.py** (1030 lines) — Interactive commands: look, talk, search, move
- **redis_bridge.py** (306 lines) — Publishes events to Redis pub/sub
- **test_bridge_subscriber.py** — Test subscriber for Redis events

### World Director (`world_director/`)
- **world_evolver.py** — Evolves the world state over time

### Cobalt Dashboard (`cobalt_dashboard/`)
- **app.py** — FastAPI backend with REST + SSE endpoints
- **index.html** — D3.js-powered UI with force-directed world map

## Data Flow

```
Config/YAML → Entity Store → Narrative Engine → Roleplay Engine → Redis Bridge
                  │                                      │
                  ▼                                      ▼
            entities.json                         timeline.jsonl
                  │                                      │
                  └──────────┬───────────────────────────┘
                             │
                             ▼
                    Cobalt Dashboard
                    (reads JSON files + Redis SSE)
```

## Redis Event Channels

| Channel | Event Type | Publisher |
|---------|-----------|-----------|
| `bring:npc_spoke` | NPC dialogue | Roleplay Engine |
| `bring:npc_moved` | NPC relocation | Roleplay Engine |
| `bring:player_moved` | Player movement | Roleplay Engine |
| `bring:scene_enter` | Entity enters location | Roleplay Engine |
| `bring:scene_exit` | Entity exits location | Roleplay Engine |
| `bring:story_beat` | Narrative event | Narrative Engine |

## Phases Completed

| Phase | Name | Status |
|-------|------|--------|
| 0 | Diagnostics | ✅ |
| 1 | FAISS + Embeddings | ✅ |
| 2 | Ollama Integration | ✅ (replaced by Mistral in Phase 4) |
| 3 | Post-restart Recovery | ✅ |
| 4 | Mistral API Migration | ✅ |
| 5 | Bug Fixes (Director, Embeddings, Graph) | ✅ |
| 5b | Fork Documentation | ✅ |
| 6 | Interactive Simulation | ✅ |
| 7 | Redis Bridge | ✅ |
| 8 | Cobalt Dashboard | ✅ |
| 9 | Production Deployment (VPS) | 🔜 Planned |
| 10 | SkyRift MMO Integration | 🔜 Future |

## World: Aethra — The Shattered Sky

- **32 entities**: 5 Characters, 5 Factions, 6 Locations, 4 Items, 4 Events, 4 Races, 4 World Rules
- **Timeline**: 200+ narrative events recorded
- **LLM**: Mistral small-latest (text + embeddings)
- **Storage**: SQLite + JSON + FAISS embeddings

## Key Characters

| Name | Role |
|------|------|
| Kaelen Ashvale | Protagonist, Weaver |
| Elara Moonshard | Companion, Aetherkin |
| Valdris Korr | Inquisitor-General, antagonist |
| Gearmaster Thunk-7 | Tech faction leader |
| Sylva Thornheart | Thornfolk leader |

## Running

```bash
# Start the world
python3 world_cli.py play

# Run dashboard
cd cobalt_dashboard
pip install fastapi uvicorn
nohup python3 app.py > cobalt.log 2>&1 &
```

## LLM Configuration

Set in `.env`:
```
WORLD_LLM_BASE_URL=https://api.mistral.ai/v1
WORLD_LLM_MODEL=mistral-small-latest
MISTRAL_API_KEY=your_key
```
