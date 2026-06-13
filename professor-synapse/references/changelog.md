# Changelog

Version history for the Professor Synapse skill. Check this after fetching updates to see what changed.

---

## v2.2.0 — 2026-06-13

- **Confidence now carries its basis.** Beyond the `high`/`medium`/`low` level, a record can record *why* it's there, in three buckets: `source` (evidence held — now surfaced in recall), and two new fields `verify` (the upgrade path — what evidence is available and how to get it) and `unknowns` (genuine gaps / unknown-unknowns). New `--verify`/`--unknowns` flags on `add`/`update`/`record` (and `--source` is now documented as the evidence-held bucket). All three are full-text indexed (so `recall --query "how to confirm employer"` surfaces the `verify` path) and surfaced on every recall hit, so the agent can justify a level and offer to confirm a shaky one ("low confidence — only mentioned once; I can verify via the HubSpot record"). Explanatory only — they don't change ranking. Additive columns; existing dbs gain them in place on first connect; the shipped seed db was regenerated to the current schema. The recall column-fetch indices and the transient FTS table grew accordingly (BM25 now 11 columns). Four new tests (55 total).
- **Write-time duplicate/contradiction check + a "when to ask vs. just save" policy.** New read-only `check --kind --text [--tags --people]` verb probes whether a proposed record resembles something stored, returning the most similar records plus `has_duplicate` (near-identical text, via a `difflib` overlap ratio ≥ `DUP_RATIO`) and `has_conflict` (a high-confidence `fact`/`decision` on the same subject a write might supersede). `record` runs the same check automatically and prints a non-blocking `⚠` advisory when it fires. `memory-protocol.md` gains a "When to ask vs. just save" section — the two-questions → three-gates model (just-save / save-low-confidence-and-narrate / ask-first), `confidence` as the release valve, and confirm-in-a-batch-at-persist — and the 🧠 Memory Keeper guidelines fold it in. Read-only, transient FTS + difflib, **no schema change**. Seven new tests (51 total).
- **Committed self-check (`references/self-check.md`).** A repeatable PASS/FAIL verification of an install — version marker, summoning (happy path + ambiguity + no-match exit 3), the memory loop (recall reinforces and reads the real store, `validate`/`doctor` clean, `forget` retires a throwaway probe), and both test suites — replacing the previously ad-hoc test prompt. Includes a ready-to-paste "Prompt for Claude" block. The update- and rebuild-protocols now end by pointing at it, and it's listed in the SKILL.md resource table.

## v2.1.0 — 2026-06-13

- **Programmatic agent summoning (`scripts/summon.py`).** Summoning is now one command instead of a manual checklist: `python3 scripts/summon.py "<agent or task>" [--query "terms"]` resolves the agent (exact slug or fuzzy match on name/triggers/description), then assembles a **boot package** whose stdout IS the summon — (1) the agent's full persona/instructions, (2) memory recalled for it inline (it shells out to `memory.py brief --agent <slug> --query ...`, **reinforcing by default** so summoning wires the surfaced memories and resets their staleness, stamped to the agent; `--no-reinforce` for a read-only peek), and (3) the resources it can load, auto-extracted from the agent's own `## Scripts` table and the references it cites, enriched with the SKILL.md "when/what" descriptions. `--query` falls back to the agent's triggers so a bare summon still recalls context; `--json` emits the package as structured data; no/ambiguous matches list candidates or point at agent creation. `references/summon-agent-protocol.md` and the SKILL.md summoning section were rewritten script-first (the script does the file-read + recall so they can't be skipped; the failure-mode table stays as guardrails, plus a manual fallback for when code execution is off). New `scripts/test_summon.py` — 12 stdlib tests against isolated temp skill roots.
- **Memory guidance rewritten to teach reasoning, not just commands.** `memory-protocol.md` now opens with the loop (recall → reason → act → capture → maintain → persist) and adds a "Reading recall results" section: how to interpret the `why` field (`matches` vs `due date reached` vs `linked to a match`), honour `constraints` before acting, calibrate trust by `confidence`, reconcile conflicts, and synthesise a cluster rather than reciting rows. Capture gains a kind-selection table (`fact`/`decision`/`note`/`lesson`) and graph best-practice notes (when to lean on default reinforce vs explicit `reinforce`/`link`/`--no-reinforce`). The 🧠 Memory Keeper agent and the SKILL.md Memory section were updated to match.
- **Knowledge graph: co-recall affinity + spreading-activation recall.** Memories can now be linked into an undirected weighted graph (new `edge` table). Edges form explicitly (`link`/`unlink`/`links`) or by co-use — **`recall`/`brief --query` reinforce by default** (bumping affinity across every pair of query matches; pass `--no-reinforce` for a read-only query), and `reinforce --ids ...` is the explicit form. Hebbian: surfaced together → wired together. Weights **decay** with a half-life (`EDGE_HALFLIFE_DAYS`), so the graph re-clusters around what's currently active. Recall now fuses a third signal (`W_GRAPH`): it seeds from the top text hits and spreads one hop along strong edges, so a memory wired to your query surfaces even on a weak text match (`"why": "linked to a match"`). With no edges, ranking is unchanged.
- **"Use it or lose it" cleanup.** Records carry `last_used`, reset on every reactivation (any `recall`/`brief` that surfaces them, `reinforce`, or `link`). `scan` now also returns `stale_longterm` — long-term records unused for `LONGTERM_STALE_DAYS` (60) **and** not well-connected (decayed connectivity below `GRAPH_SPARE_AFFINITY`); well-wired records are spared. New `forget --ids` verb retires chopping-block records (marked `dropped`, edges removed). `doctor` reports `edge_rows` and flags dangling edges; `export` includes edges. Eleven new tests (43 total).
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
