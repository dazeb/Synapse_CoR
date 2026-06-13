# Changelog

Version history for the Professor Synapse skill. Check this after fetching updates to see what changed.

---

## 2026-06-13

- **Memory system**: Professor Synapse now remembers across sessions through one shared, agent-tagged store. New `scripts/memory.py` (stdlib-only CLI), `references/memory-protocol.md` (recall/capture/janitor), and `references/memory-data-model.md` (schema + migration rules)
- **🧠 Memory Keeper agent**: New `agents/memory-agent.md` — the persistence layer other agents lean on; directly summonable for recall/capture/cleanup
- **Memory store seeded**: `memory/memory.json` (clean working-memory seed) and `memory/longterm.db` (empty SQLite long-term store + change log)
- **Ranked-fusion recall**: `recall --query` retrieves with SQLite FTS5 (stemming + prefix + column-weighted BM25 — `people`/`tags` hits outrank free text) then re-ranks by fusing relevance + recency + record kind via Reciprocal Rank Fusion. `dropped` records are excluded. Index is built transiently at query time (no schema change/migration); falls back to `LIKE` if FTS5 is unavailable. Tuning knobs (`RRF_K`, `W_TEXT`, `W_RECENCY`, `BM25_WEIGHTS`, `KIND_WEIGHT`) are constants near the top of `memory.py`. Vector/embedding search was evaluated and rejected as overkill (see `memory-data-model.md`)
- **`brief` verb**: One-shot start-of-session prefetch — profile + active items + due long-term items in a single call, plus `--query` for fused ranked matches
- **Test suite**: `scripts/test_memory.py` — 25 stdlib `unittest` cases (no pip) covering CRUD, archive/resurface, due recall, FTS stemming/prefix/column-weighting, fusion ordering, dropped-exclusion, LIKE fallback, `brief`, scan, validate-fix, doctor, and the migration guard. Each test runs against an isolated temp root. Run: `python3 scripts/test_memory.py`
- **Agent summoning protocol extracted**: New `references/summon-agent-protocol.md` makes "summoning = read the file and become the agent" explicit, with common failure modes. SKILL.md workflow and resource table now point to it
- **SKILL.md**: Added `## Memory` and `## Agent Summoning Protocol` sections; resource table clarifies the INDEX → agent-file → become-the-agent flow
- **Update protocol**: New "Memory Store: Special Handling" section — on update, preserve the local `memory/` store byte-for-byte (never overwrite with the canonical seed), update only the memory code/protocols; covers first-time setup (the binary `longterm.db` is created by `memory.py`, never fetched) and post-update `validate`/`doctor` checks

## 2026-04-02

- **GitHub blob parser fix**: Updated `github_blob_parser.py` to handle GitHub's reorganized JSON payload structure (`payload.codeViewBlobRoute.richText` and `payload['codeViewBlobLayoutRoute.StyledBlob'].rawLines`), with fallback to legacy paths
- **Packaging workflow enforcement**: Added mandatory packaging workflow section to SKILL.md — impossible to miss
- **Two-tier learned patterns**: Global patterns now live directly in SKILL.md; domain-specific patterns live in each agent's own Learned Patterns section
- **Agent template updated**: Learned Patterns section (Effective Patterns / Anti-Patterns) added to agent template with format templates
- **rebuild-index.sh**: Auto-appends Learned Patterns section to any agent file missing it
- **Removed `references/learned-patterns.md`**: Content moved into SKILL.md's Global Learned Patterns section
- **Changelog added**: This file — tracks version changes for the update protocol

## 2026-01-30

- Initial release with domain researcher agent, convener protocol, and update/rebuild protocols
