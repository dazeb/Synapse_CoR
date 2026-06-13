# Changelog

Version history for the Professor Synapse skill. Check this after fetching updates to see what changed.

---

## Unreleased

- **Richer memory body + `lesson` kind.** Records and active items gain four optional fields: `goal` (what it serves), `outcome` (what resulted), `constraints` (a list of gotchas — each a quoted phrase, not comma-split), and `confidence` (`high`/`medium`/`low`). A new `lesson` kind captures a reusable how-to learned by doing and conventionally fills all four. `goal`/`outcome`/`constraints` are full-text indexed (so recall matches a gotcha directly), and `confidence` + `kind` apply multiplicative nudges in the ranked-fusion recall. `kind` is now validated in Python instead of by a DB CHECK; existing long-term dbs upgrade in place on first connect (new columns added; the table rebuilt once to drop the old `kind` CHECK, preserving every row). New CLI flags: `--goal`, `--outcome`, `--constraints`, `--confidence` on `add`/`update`/`record`. Six new tests (32 total).
- **Tag/people parsing accepts comma- or space-separated values.** `--tags test,install` now stores two distinct tags (`["test", "install"]`), the same as `--tags test install`. Previously a comma-separated string landed as one tag. Normalization applies to all list-valued options (`--tags`, `--people`, `--query`, `--focus-areas`, `--archive`, `--drop`). Added a regression test (26 cases total).

## v2.0.0 — 2026-06-13

Major version marking the memory architecture and the script-driven update pipeline as the new baseline. Consolidates the v1.1.0 memory work with a one-command updater and removes the legacy HTML-scraping update path.

**Breaking / behavioral:**

- **Removed the legacy HTML blob scrapers** (`scripts/fetch-github-file.sh`, `scripts/github_blob_parser.py`) and the `html2text` dependency. Updates no longer scrape GitHub blob pages file-by-file; the canonical codeload tarball is the only fetch path. Anything that called those scripts directly must switch to `scripts/update.sh`.
- **Update mechanism is now script-driven.** `references/update-protocol.md` leads with `scripts/update.sh`; the hand-run codeload sequence is kept only as an under-the-hood reference.

**Added:**

- **`scripts/update.sh`** — one command does the whole update: detects the latest release tag (`releases/latest`), downloads the canonical codeload tarball (pinned to the tag, falling back to `main`), overlays your local `memory/` store and custom agents, flags `SKILL.md`/changed shared agents as `*.local-MERGE` for hand-merging, and rebuilds `INDEX.md`. Supports `--check`, `--ref`, `--out`, `--force`. It prepares the merged tree but does not install — you still package and click "Copy to your skills".

**Carried forward from v1.1.0 (the memory system, now part of the 2.0 baseline):**

- Shared, agent-tagged memory store via `scripts/memory.py` (working memory + SQLite long-term + change log), with `references/memory-protocol.md` and `references/memory-data-model.md`.
- Ranked-fusion recall (SQLite FTS5 + column-weighted BM25, re-ranked by recency and record kind via RRF; `LIKE` fallback) and the one-shot `brief` prefetch verb.
- 🧠 Memory Keeper agent and a 25-case stdlib test suite (`scripts/test_memory.py`).

**Docs:** `scripts-protocol.md` catalog and `README.md` updated to match; `SKILL.md` bumped to 2.0.0.

## v1.1.0 — 2026-06-13

- **Memory system release.** SKILL.md now carries a `**Version:**` marker for precise update detection against the latest release tag.
- **Update protocol rewritten around codeload**: updates now download the canonical repo as a single `codeload.github.com` source tarball (pinned to the release tag, falling back to `main`), extract, merge, and rebuild — replacing the fragile per-file HTML blob-scraping, which is demoted to a legacy fallback. Host reachability was verified in the sandbox: `codeload.github.com` works; release **assets** (`objects`/`release-assets.githubusercontent.com`) are proxy-blocked, so release-asset downloads are not used. `releases/latest` (on `github.com`) drives version detection. The "Reachable Hosts" table documents the proxy-vs-real-host `x-deny-reason` distinction.

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
