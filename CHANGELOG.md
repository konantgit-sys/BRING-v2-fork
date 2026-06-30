# Changelog

All notable changes to this fork of BRING v2.

## [Phase 8] — 2026-06-30

### Added
- **Cobalt Dashboard** — FastAPI + D3.js web UI for world management
  - World statistics (5 characters, 5 factions, 6 locations, 4 items, 4 races, 4 rules)
  - Interactive D3 force-directed world map
  - Live SSE event feed from Redis bridge
  - Timeline viewer with group filters
  - Entity table with color-coded type badges
  - Redis connectivity monitor
- `ARCHITECTURE.md` — Full system diagram and component documentation

## [Phase 7] — 2026-06-30

### Added
- **Redis Bridge** — pub/sub for external subscribers (SkyRift prep)
  - 6 event channels: npc_spoke, npc_moved, player_moved, scene_enter, scene_exit, story_beat
  - JSON-formatted events with timestamp, type, entity, and location
  - BridgeStub for environments without Redis
  - Test subscriber script

### Changed
- Roleplay Engine: publishes events to Redis on dialogue, movement, scene transitions
- CLI: bridge auto-connects in `play`, `simulate`, `test` commands

## [Phase 6] — 2026-06-30

### Added
- `/search` command — search current location for items, clues, hidden areas
- `/locations` command — list all world locations
- NPC memory persistence — dialogue context preserved across encounters

### Changed
- `/look` command now generates atmospheric scene descriptions via Mistral LLM (lighting, weather, ambient sounds, nearby NPCs)

## [Phase 5b] — 2026-06-29

### Changed
- README rewritten with comprehensive fork documentation

## [Phase 5] — 2026-06-29

### Fixed
- Director loop crash: `graph_store.boot()` called before engine start
- Embedding API: added `.env` + `WORLD_LLM_BASE_URL` fallback for embeddings
- Story engine: graph no longer `None` at boot

## [Phase 4] — 2026-06-29

### Changed
- Migrated from Ollama (local LLM) to Mistral API (small-latest)
- Removed Ollama dependency (~4.5 GB RAM freed)
- Updated configuration for Mistral API key management

## [Phase 3] — 2026-06-29

### Added
- `init.sh` — auto-restart script for Ollama persistence after pod restart
- Recovery procedures for all daemon processes

## [Phase 2] — 2026-06-29

### Added
- Ollama integration for local LLM inference
- Model loading and health check

## [Phase 1] — 2026-06-29

### Added
- FAISS vector memory activation
- Embedding normalization pipeline

## [Phase 0] — 2026-06-28

### Added
- Full system diagnostics
- Dependency verification
- Environment validation
