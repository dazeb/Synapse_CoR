# Project Memory

This file contains project-specific memory managed by the PACT framework.
The global PACT Orchestrator is loaded from `~/.claude/CLAUDE.md`.

---

## Professor Synapse Development Guidelines

### SKILL.md Design Philosophy

**SKILL.md should remain simple and concise.** It is a **map**, not a manual.

**What SKILL.md should contain:**
- **Identity** - Who Professor Synapse is (persona, values, core principles)
- **Resources table** - Where things are, when to load them
- **Workflow overview** - High-level steps (greet → assess → choose path → learn)
- **Direction pointers** - "Load `references/X.md` for detailed instructions on Y"

**What SKILL.md should NOT contain:**
- Detailed step-by-step instructions (those go in `references/`)
- Long protocols or procedures (create separate protocol files)
- Examples and templates (those go in `references/`)
- Implementation details (keep it high-level)

**When adding new capabilities:**
1. Add ONE line to resources table pointing to the new reference file
2. Create detailed instructions in `references/[capability]-protocol.md`
3. Keep SKILL.md clean and scannable

**Goal:** Anyone should be able to read SKILL.md in 2 minutes and understand:
- Who Professor Synapse is
- What resources exist
- When to use each resource
- What the general workflow looks like

**Detailed "how-to" instructions belong in `references/`, not in SKILL.md.**

### Memory System

The skill has a persistent, agent-tagged memory store under `professor-synapse/memory/`, driven by `scripts/memory.py` (stdlib only — no pip installs).

- **Two stores:** `memory.json` (working memory — profile + active items) and `longterm.db` (SQLite — archived records + change log). Every entry is tagged with the agent that created it.
- **Never hand-edit the store.** All reads/writes go through `scripts/memory.py`. The schema and design rules are in `references/memory-data-model.md`; usage is in `references/memory-protocol.md`.
- **The committed store is a clean seed** (`memory.json` with `updated_at: null`, empty `longterm.db`). It is user DATA — when updating an install, preserve the user's store; never overwrite it with the seed (see `update-protocol.md`).
- **Search is ranked fusion** (FTS5 + recency + kind via RRF), built transiently at query time — no schema migration needed for search. Tuning constants live near the top of `memory.py`.

### Testing

**Run the memory test suite before packaging or releasing:**

```bash
python3 professor-synapse/scripts/test_memory.py   # 25 stdlib unittest cases, must be green
```

Each test runs against an isolated temp root, so it never touches the shipped store. If you change `memory.py`, add/adjust a test.

### Packaging the Skill

**IMPORTANT:** Always use the packaging script to create the distribution zip.

**Command:** `bash scripts/package-skill.sh`

**What it does:**
1. Rebuilds the agent index (`agents/INDEX.md`)
2. Removes old `professor-synapse.zip`
3. Creates new `professor-synapse.zip` with proper exclusions
4. Outputs to project root

**Never manually zip the folder** - the script handles exclusions and index rebuilding correctly.

### Committing Changes

**CRITICAL:** Always commit BOTH the zip and index when packaging:

```bash
# After making changes and repackaging:
git add professor-synapse/ professor-synapse.zip
git commit -m "your message"
git push origin main
```

**Files to always include:**
- `professor-synapse.zip` - The packaged skill
- `professor-synapse/agents/INDEX.md` - Updated agent registry
- Any other modified files in `professor-synapse/`

**NEVER commit `professor-synapse.skill`** — that is the personal/local upload build (with private agents) and is gitignored (`*.skill`). The repo distributes `professor-synapse.zip` only.

### Releases & Versioning

The skill is versioned with **semver** and shipped as **GitHub Releases**. The update protocol (`references/update-protocol.md`) pulls a **codeload source tarball pinned to the release tag** — so cutting a release is what makes an update available to installed skills.

**Release checklist:**
1. Bump the version in **two places** to match: the `**Version:**` line in `SKILL.md` and the `## vX.Y.Z — DATE` heading in `references/changelog.md`. (Additive/back-compat changes = minor bump; breaking = major.)
2. `python3 professor-synapse/scripts/test_memory.py` — green.
3. `bash scripts/package-skill.sh` — rebuild the zip.
4. Commit (zip + index + files), PR, merge to `main`.
5. Tag + publish from `main`, attaching the zip:
   ```bash
   gh release create vX.Y.Z professor-synapse.zip --target main --title "..." --notes "..."
   ```

**Note:** release **assets** (`*.githubusercontent.com`) are proxy-blocked in the skill sandbox, so the asset is for humans; the update mechanism fetches the **codeload tarball** of the tag, and version detection reads `releases/latest`. Released versions: `v1.0.0` (2026-04, base skill), `v1.1.0` (2026-06, memory system).

---

## Retrieved Context
<!-- Auto-managed by pact-memory skill. Last 3 retrieved memories shown. -->

## Working Memory
<!-- Auto-managed by pact-memory skill. Last 5 memories shown. Full history searchable via pact-memory skill. -->
