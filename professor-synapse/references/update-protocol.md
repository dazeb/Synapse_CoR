# Update Protocol: Safely Merging Skill Updates

## Purpose

This protocol lets users pull updates to the Professor Synapse skill **without overwriting their customizations** (custom agents, learned patterns, and especially their `memory/` store).

**Critical Understanding:** Skills cannot be edited in place. To update a skill you:
1. Download the canonical repo (one tarball)
2. Merge it with the user's local customizations
3. **Rebuild the entire skill** as a new package
4. User replaces the old skill via the "Copy to your skills" button

You are performing a **smart merge and rebuild**, not a blind overwrite.

---

## The Canonical Source

**GitHub Repository:** `https://github.com/ProfSynapse/Professor-Synapse`
**Skill Location:** `professor-synapse/` folder inside the repo

---

## Reachable Hosts (important)

The sandbox network uses an **allowlist**, and a blocked host returns a proxy `403` with header `x-deny-reason: host_not_allowed` — which looks like a real response. **Distinguish a real-host status from a proxy denial by checking for that header**, not by the status code alone.

Verified in the skill sandbox:

| Host | Status | Use |
|------|--------|-----|
| `github.com` | ✅ reachable | HTML pages, redirects, `releases/latest` (version detection) |
| `codeload.github.com` | ✅ reachable | **Download the whole repo as a tarball — the primary fetch** |
| `raw.githubusercontent.com` | ⚠️ environment-dependent | Per-file raw fetch; verify before relying (some environments block it) |
| `objects.githubusercontent.com` | ❌ blocked (proxy) | Release **assets** — do NOT use |
| `release-assets.githubusercontent.com` | ❌ blocked (proxy) | Release **assets** — do NOT use |
| `api.github.com` | ❌ blocked (proxy) | — |
| `cdn.jsdelivr.net`, `raw.githack.com` | ❌ blocked | — |

**Consequence:** GitHub serves release *assets* from `*.githubusercontent.com`, which is blocked — so you **cannot download a release `.zip`/`.tar.gz` asset**. Use the **codeload source tarball** instead. Releases are still used, but only for **versioning** (the tag) and **version detection** (`releases/latest`), never for the asset download.

---

## Primary Method: `scripts/update.sh`

One script does the whole fetch-and-merge. It detects the latest release, downloads the canonical codeload tarball, and builds a merged tree that **preserves your `memory/` store and custom agents** — then stops so you can package it. It never installs.

```bash
# See whether an update exists (no changes made)
bash scripts/update.sh --check

# Build the merged update tree (default output: /tmp/ps-update)
bash scripts/update.sh
#   --ref <tag|branch>   fetch a specific tag/branch (default: latest release, else main)
#   --out <dir>          where to build the merged tree
#   --force              rebuild even if already current
```

What it does, in order: reads the local `**Version:**` from `SKILL.md`; resolves the latest tag via `releases/latest`; downloads `codeload.github.com/.../tar.gz/<ref>`; overlays your local `memory/memory.json` + `memory/longterm.db` and any custom agents onto the canonical tree; flags `SKILL.md` and any changed shared agents as `*.local-MERGE` files for you to hand-merge Learned Patterns; and rebuilds `agents/INDEX.md`. It prints exactly what it preserved and what needs a manual merge.

**After it runs:**
1. Resolve any `*.local-MERGE` files it flagged (port your Learned Patterns into the canonical file, then delete the `.local-MERGE`).
2. Confirm the store loads against the new code:
   ```bash
   cd /tmp/ps-update
   python3 scripts/memory.py validate   # working memory structure
   python3 scripts/memory.py doctor      # long-term db integrity
   ```
3. Package the merged tree with skill-creator (see `rebuild-protocol.md`). The user clicks **"Copy to your skills"** to replace — you cannot do this programmatically.

The rest of this document explains what the script does under the hood, for transparency or when you need to run a step by hand.

---

## Manual Equivalent (what the script does)

One download gets the entire canonical skill — no per-file fetching, no HTML parsing.

### Step 1: Detect the latest version

`releases/latest` redirects to the newest tag (on `github.com`, reachable):

```bash
curl -sSL -o /dev/null -w '%{url_effective}\n' \
  https://github.com/ProfSynapse/Professor-Synapse/releases/latest
# -> https://github.com/ProfSynapse/Professor-Synapse/releases/tag/v1.1.0   (parse the tag)
```

Compare that tag to the local `**Version:**` line in `SKILL.md`. If they match, the skill is current — tell the user and stop. If `releases/latest` 404s (no releases yet), fall back to the `main` branch.

### Step 2: Download and extract the tarball

Pin to the release tag for a reproducible snapshot; fall back to `main` when there is no release:

```bash
TAG=v1.1.0   # from Step 1; or use refs/heads/main as a fallback
REF="refs/tags/$TAG"   # fallback: REF="refs/heads/main"

curl -sSL -o /tmp/ps.tar.gz \
  "https://codeload.github.com/ProfSynapse/Professor-Synapse/tar.gz/$REF"

mkdir -p /tmp/ps-canonical
tar -xzf /tmp/ps.tar.gz -C /tmp/ps-canonical --strip-components=1
# Canonical skill now at: /tmp/ps-canonical/professor-synapse/
```

`--strip-components=1` removes the tarball's top-level `Professor-Synapse-<ref>/` wrapper, so the skill lands at `/tmp/ps-canonical/professor-synapse/`.

### Step 3: Check the changelog

```bash
cat /tmp/ps-canonical/professor-synapse/references/changelog.md
```

Summarize what changed for the user before merging.

### Step 4: Merge in local customizations

Start from the canonical tree and layer the user's content back on top. **The `memory/` store is the critical one — see "Memory Store: Special Handling".**

```bash
SRC=/tmp/ps-canonical/professor-synapse           # canonical (new)
DST=/mnt/skills/user/professor-synapse            # current install
MERGED=/tmp/ps-merged

cp -R "$SRC" "$MERGED"

# 1. Preserve the user's memory store byte-for-byte (NEVER take canonical's seed)
if [ -d "$DST/memory" ]; then
  cp -f "$DST/memory/memory.json"  "$MERGED/memory/" 2>/dev/null || true
  cp -f "$DST/memory/longterm.db"  "$MERGED/memory/" 2>/dev/null || true
fi

# 2. Preserve custom agents (present locally, absent from canonical)
for f in "$DST"/agents/*.md; do
  name=$(basename "$f")
  [ -e "$SRC/agents/$name" ] || cp "$f" "$MERGED/agents/$name"
done
```

Then, by hand:
- **SKILL.md** — merge the user's `## Global Learned Patterns` into the canonical SKILL.md (keep their patterns, adopt structural changes).
- **Agent files** — when a shared agent updated, preserve the user's `## Learned Patterns` entries.
- Note any other local modifications to system files before overwriting them.

See **File Categories** below for the per-file rules.

### Step 5: Rebuild

```bash
cd "$MERGED" && bash scripts/rebuild-index.sh   # regenerate agents/INDEX.md
```

Then follow **`rebuild-protocol.md`** to package `$MERGED` with skill-creator and present it. The user clicks **"Copy to your skills"** to replace — you cannot do this programmatically.

If the install had no `memory/` before this update, it is being introduced — see **"Memory Store: Special Handling → First-time setup"**.

---

## File Categories

Different files have different update rules:

| Category | Files | Update Rule |
|----------|-------|-------------|
| **System Core** | `SKILL.md`, `scripts/*` | Apply canonical. SKILL.md holds Global Learned Patterns — smart-merge to preserve the user's |
| **Reference Protocols** | `references/*.md` | Apply canonical (show diff) |
| **Template** | `references/agent-template.md` | Apply canonical (usually safe) |
| **User Content** | `agents/*` (except domain-researcher, memory-agent) | NEVER overwrite — user's custom agents |
| **System Agent** | `agents/domain-researcher.md`, `agents/memory-agent.md` | Apply canonical (show diff) |
| **Auto-generated** | `agents/INDEX.md` | Don't merge — regenerated by `rebuild-index.sh` |
| **Memory Store** | `memory/memory.json`, `memory/longterm.db` | User DATA — NEVER overwrite an existing store. See below |

---

## Memory Store: Special Handling

The memory architecture (added 2026-06) lives in a `memory/` directory and is wired through `scripts/memory.py`. An update touches the *code and protocols* of memory, **never the data**. Treat `memory/` exactly like a user's custom agents: it holds what Professor Synapse has remembered, and it must survive the update intact.

**The memory feature is made of two different kinds of file:**

| Part | Files | On update |
|------|-------|-----------|
| **Code & protocols** | `scripts/memory.py`, `references/memory-protocol.md`, `references/memory-data-model.md`, `agents/memory-agent.md` | Apply from canonical (same as any system file) |
| **The store (user data)** | `memory/memory.json`, `memory/longterm.db` | **Preserve the local copy byte-for-byte. Never overwrite with canonical.** |

### Updating an install that already has memory

1. Apply the **code & protocol** files normally.
2. **Carry the user's existing `memory/` directory into the merged build unchanged** (Step 4 above copies `memory.json` and `longterm.db` across). The canonical store is an empty seed and would wipe the user's memory.
3. After the new `scripts/memory.py` is in place, confirm the store still loads against the new code:
   ```bash
   python3 scripts/memory.py validate   # working memory structure
   python3 scripts/memory.py doctor      # long-term db integrity
   ```
   If a release bumped the schema, migration runs automatically on the next load (see `references/memory-data-model.md`). Writes back up to `memory.json.bak` and replace atomically, so a version mismatch fails loud rather than corrupting data.

### First-time setup (install had no memory before)

Older installs predate the `memory/` directory. For them the update *introduces* memory. The tarball already contains the seed `memory/memory.json` and an empty `memory/longterm.db`, so a normal merge brings them in. If you ever need to recreate the store from scratch, let the script do it (never fetch the binary db):

```bash
python3 scripts/memory.py read       # creates memory/memory.json (clean seed)
python3 scripts/memory.py doctor      # creates memory/longterm.db (empty schema)
```

### Why this matters

`memory/` is the one place in the skill where the user's data accumulates. Blindly overwriting it with the canonical copy is the single most destructive mistake this protocol exists to prevent. When in doubt: **keep the local `memory/`, update everything around it.**

---

## Fallback: no releases yet

If `releases/latest` 404s (the repo has no releases), `update.sh` automatically falls back to the `main` branch tarball — same merge logic, just an unpinned ref. If `codeload.github.com` itself is ever blocked in some environment, run the **Manual Equivalent** steps above by hand against `refs/heads/main`; there is no per-file scraping path anymore.

---

## When to Use This Protocol

**Updating from the canonical repo:**
- User says "check for updates" or "update the skill"
- Version detection shows a newer release than the local `**Version:**`
- User wants new features from canonical

**Adding new local content:** creating an agent, script, or reference file — any structural change requires a rebuild (see `rebuild-protocol.md`).

---

## Safety Principles

### Never Blind Overwrite
- Always show what's changing before rebuilding
- Always preserve the user's custom content **and `memory/` store**
- Always ask before removing anything

### Smart Merge Strategy
1. **New features** — add from canonical (low risk)
2. **Modified system files** — use canonical, show the user what changed
3. **Hybrid files** (SKILL.md, shared agents) — merge, preserving the user's learned patterns
4. **User files & memory store** — always preserve

### The Rebuild Workflow
You prepare and build the merged package; the **user clicks the button** to replace. You cannot install it for them.

---

## Quick Reference

### Complete Update Workflow

```bash
# 1. Check, then build the merged tree (preserves memory/ + custom agents, rebuilds INDEX.md)
bash scripts/update.sh --check
bash scripts/update.sh                      # output: /tmp/ps-update

# 2. Resolve any *.local-MERGE files it flagged (port Learned Patterns, then delete them)

# 3. Sanity-check the carried-over store
cd /tmp/ps-update && python3 scripts/memory.py validate && python3 scripts/memory.py doctor

# 4. Package /tmp/ps-update with skill-creator (rebuild-protocol.md); user clicks "Copy to your skills"
```

**Golden rule:** preserve the local `memory/` store and custom agents; never overwrite them with canonical.

**Do NOT attempt** (proxy-blocked): `objects.githubusercontent.com`, `release-assets.githubusercontent.com` (release assets), `api.github.com`, `cdn.jsdelivr.net`, `raw.githack.com`.

---

## Dependencies

- `curl`, `tar`, `bash` (standard on the sandbox) — used by `scripts/update.sh`
- `python3` (for `memory.py` validation after merge)
