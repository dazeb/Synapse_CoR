# Update Protocol: Safely Merging Skill Updates

## Purpose

This protocol allows users to pull updates to the Professor Synapse skill **without overwriting their customizations** (custom agents, learned patterns, local modifications).

**Critical Understanding:** Skills cannot be edited in place. To update a skill, you must:
1. Fetch updates from the canonical repo
2. Merge with user's local customizations
3. **Rebuild the entire skill** as a new package using skill-creator
4. User replaces the old skill with the new one via "Copy to your skills" button

You are performing a **smart merge and rebuild**, not a blind overwrite or in-place edit.

---

## The Canonical Source

**GitHub Repository:** `https://github.com/ProfSynapse/Professor-Synapse`
**Skill Location:** `professor-synapse/` folder

---

## Fetching From GitHub

### The Problem

Claude's network blocks these domains:
- `api.github.com` (403 host_not_allowed)
- `raw.githubusercontent.com` (403 host_not_allowed)
- `cdn.jsdelivr.net` (connection refused)
- `raw.githack.com` (connection refused)

### The Solution

GitHub embeds file content as JSON within the blob page HTML. We can:
1. Fetch the blob page via `curl` (github.com is allowed)
2. Parse the embedded JSON from `<script type="application/json" data-target="react-app.embeddedData">`
3. Extract `payload.codeViewBlobRoute.richText` (rendered HTML) or `payload['codeViewBlobLayoutRoute.StyledBlob'].rawLines` (for non-markdown), with fallback to legacy `payload.blob` paths
4. Convert HTML to Markdown using `html2text`
5. Post-process for clean formatting (fix code blocks, horizontal rules, etc.)

### Using the Fetch Script

Two scripts work together in the `scripts/` folder:
- `fetch-github-file.sh` - Bash wrapper (handles arguments, curl, output)
- `github_blob_parser.py` - Python parser (extracts and cleans content)

**Fetch a single file to stdout:**
```bash
bash scripts/fetch-github-file.sh ProfSynapse/Professor-Synapse main professor-synapse/SKILL.md
```

**Fetch and save to a file:**
```bash
bash scripts/fetch-github-file.sh ProfSynapse/Professor-Synapse main professor-synapse/references/convener-protocol.md /tmp/convener.md
```

**Using full URL:**
```bash
bash scripts/fetch-github-file.sh "https://github.com/ProfSynapse/Professor-Synapse/blob/main/professor-synapse/SKILL.md"
```

### Listing Repository Contents

To discover what files exist in the repo:

```bash
# List top-level structure
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse" | grep -o 'professor-synapse/[^"]*' | sort -u

# List agents
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse/agents" | grep -o 'professor-synapse/agents/[^"]*\.md' | sort -u

# List references
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse/references" | grep -o 'professor-synapse/references/[^"]*\.md' | sort -u

# List scripts
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse/scripts" | grep -o 'professor-synapse/scripts/[^"]*' | sort -u
```

---

## File Categories

Different files have different update rules:

| Category | Files | Update Rule |
|----------|-------|-------------|
| **System Core** | `SKILL.md`, `scripts/*` | Show diff, recommend applying updates. SKILL.md contains Global Learned Patterns — smart merge to preserve user's patterns |
| **Reference Protocols** | `references/*.md` | Show diff, offer to apply |
| **Template** | `references/agent-template.md` | Show diff, usually safe to update |
| **User Content** | `agents/*` (except domain-researcher, memory-agent) | NEVER overwrite - user's custom agents |
| **System Agent** | `agents/domain-researcher.md`, `agents/memory-agent.md` | Show diff, offer to update |
| **Auto-generated** | `agents/INDEX.md` | Don't update directly - regenerated from agents |
| **Memory Store** | `memory/memory.json`, `memory/longterm.db` | User DATA - NEVER overwrite an existing store. See "Memory Store: Special Handling" below |

---

## Memory Store: Special Handling

The memory architecture (added 2026-06) lives in a `memory/` directory and is wired through `scripts/memory.py`. An update touches the *code and protocols* of memory, **never the data**. Treat `memory/` exactly like a user's custom agents: it holds what Professor Synapse has remembered, and it must survive the update intact.

**The memory feature is made of two different kinds of file:**

| Part | Files | On update |
|------|-------|-----------|
| **Code & protocols** | `scripts/memory.py`, `references/memory-protocol.md`, `references/memory-data-model.md`, `agents/memory-agent.md` | Fetch from canonical, show diff, apply (same as any system file) |
| **The store (user data)** | `memory/memory.json`, `memory/longterm.db` | **Preserve the local copy byte-for-byte. Never overwrite with canonical.** |

### Updating an install that already has memory

1. Update the **code & protocol** files normally (fetch, diff, apply).
2. **Carry the user's existing `memory/` directory into the merged build unchanged** — copy their `memory.json` and `longterm.db` across; do not fetch or merge the canonical ones. The canonical store is an empty seed and would wipe the user's memory.
3. After the new `scripts/memory.py` is in place, confirm the store still loads against the new code:
   ```bash
   python3 scripts/memory.py validate   # working memory structure
   python3 scripts/memory.py doctor      # long-term db integrity
   ```
   If a release bumped the schema, migration runs automatically on the next load (see `references/memory-data-model.md`). Writes back up to `memory.json.bak` and replace atomically, so a version mismatch fails loud rather than corrupting data — it never silently mangles the store.

### First-time setup (install had no memory before)

Older installs predate the `memory/` directory. For them the update *introduces* memory:

1. Add the code & protocol files (`scripts/memory.py`, the two `references/memory-*.md`, `agents/memory-agent.md`) and register `memory-agent` by running `bash scripts/rebuild-index.sh`.
2. **Do not try to fetch the store files.** `longterm.db` is a **binary SQLite file** — the GitHub fetch pipeline (`fetch-github-file.sh` → `github_blob_parser.py`) only handles text/markdown and cannot retrieve it. And you don't want the canonical's seed data anyway.
3. Let the script create an empty store itself. A single read materialises both files with the correct schema:
   ```bash
   python3 scripts/memory.py read       # creates memory/memory.json (clean seed)
   python3 scripts/memory.py doctor      # creates memory/longterm.db (empty schema)
   ```
   The shipped `memory/memory.json` seed (`updated_at: null`, empty profile, empty `active`) is equivalent and may be copied instead — but the binary `longterm.db` is always created by `memory.py`, never fetched.

### Why this matters

`memory/` is the one place in the skill where the user's data accumulates. Blindly overwriting it with the canonical copy is the single most destructive mistake this protocol exists to prevent. When in doubt: **keep the local `memory/`, update everything around it.**

---

## The Update Process

### Step 1: Fetch Repository Structure

```bash
# Get file listings from canonical repo
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse" | grep -o 'professor-synapse/[^"]*' | sort -u
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse/agents" | grep -o 'professor-synapse/agents/[^"]*\.md' | sort -u
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse/references" | grep -o 'professor-synapse/references/[^"]*\.md' | sort -u
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse/scripts" | grep -o 'professor-synapse/scripts/[^"]*' | sort -u
```

### Step 2: Compare With Local

```bash
# List local skill contents
ls -la /mnt/skills/user/professor-synapse/
ls -la /mnt/skills/user/professor-synapse/agents/
ls -la /mnt/skills/user/professor-synapse/references/
ls -la /mnt/skills/user/professor-synapse/scripts/
```

Compare to identify:
- **New files** in canonical (not in local) - safe to add
- **Missing files** in canonical (user's custom content) - preserve
- **Shared files** (potentially modified) - compare before updating

### Step 3: Check the Changelog

Before comparing individual files, fetch `references/changelog.md` to see a summary of what changed:

```bash
bash scripts/fetch-github-file.sh ProfSynapse/Professor-Synapse main professor-synapse/references/changelog.md
```

This helps you make targeted updates and communicate changes to the user.

### Step 4: Fetch and Compare Files

For each file that might have updates:

```bash
# Fetch canonical version to temp location
bash scripts/fetch-github-file.sh ProfSynapse/Professor-Synapse main professor-synapse/SKILL.md > /tmp/canonical-SKILL.md

# Compare with local
diff /mnt/skills/user/professor-synapse/SKILL.md /tmp/canonical-SKILL.md
```

### Step 5: Prepare Merged Content

Create a temporary directory with the merged skill content:

1. **Start with canonical structure**
   - Fetch all system files from canonical repo
   - Use `bash scripts/fetch-github-file.sh` for each file

2. **Preserve user customizations**
   - Keep user's custom agents (not in canonical)
   - **Carry the user's `memory/` store across untouched** (`memory.json` + `longterm.db`) — never overwrite with canonical (see "Memory Store: Special Handling")
   - Merge SKILL.md's Global Learned Patterns (user patterns + new system patterns)
   - Merge agent-level Learned Patterns sections in agent files
   - Note any user modifications to system files

3. **Smart merge decisions**
   - **NEW files**: Add from canonical
   - **MODIFIED system files**: Use canonical version (show user what changed)
   - **SKILL.md**: Smart merge — preserve user's Global Learned Patterns, apply structural changes
   - **Agent files**: Preserve user's Learned Patterns entries when updating agent structure
   - **Memory store**: Always preserve the local `memory/` data; update only the memory code/protocols around it
   - **USER files**: Always preserve

**Example merge:**
```bash
# Fetch canonical to /tmp/canonical-synapse/
mkdir -p /tmp/canonical-synapse/{agents,references,scripts}

# Fetch SKILL.md
bash scripts/fetch-github-file.sh ProfSynapse/Professor-Synapse main professor-synapse/SKILL.md /tmp/canonical-synapse/SKILL.md

# Fetch references/
bash scripts/fetch-github-file.sh ProfSynapse/Professor-Synapse main professor-synapse/references/convener-protocol.md /tmp/canonical-synapse/references/convener-protocol.md
# ... repeat for all files

# Copy user's custom agents
cp /mnt/skills/user/professor-synapse/agents/custom-*.md /tmp/canonical-synapse/agents/

# Merge SKILL.md Global Learned Patterns
# (Extract user's patterns from local SKILL.md, merge into canonical SKILL.md)
```

### Step 6: Rebuild Skill with skill-creator

**CRITICAL:** You cannot edit skills in place. You must use `skill-creator` to build a new skill package.

Use the skill-creator capability to package the merged content:

```
🧙🏾‍♂️: "I've prepared the merged skill content in /tmp/canonical-synapse/ with:
- All canonical updates
- Your custom agents preserved
- Your learned patterns merged

Now I'll use skill-creator to rebuild the skill..."

[Use skill-creator tool to create skill from /tmp/canonical-synapse/]
```

The skill-creator will:
1. Package the directory as a skill zip
2. Validate the structure
3. Make it available for installation

### Step 7: Rebuild the Skill

**See `rebuild-protocol.md` for the complete rebuild workflow.**

Summary:
1. Validate merged content in /tmp/canonical-synapse/
2. Run `bash scripts/rebuild-index.sh` in the merged directory
3. Use skill-creator on the merged directory
4. User clicks "Copy to your skills" to replace

```
🧙🏾‍♂️: "✅ Merged skill content prepared!

Following the rebuild protocol to package the updated skill..."

[Follow rebuild-protocol.md steps]

"Ready to replace your skill with this updated version that includes:
- [List canonical updates]
- [List preserved customizations]"
```

**Important:** The user clicks the button—you cannot do this programmatically.

---

## When to Use This Protocol

This protocol is needed whenever the skill structure changes:

**Updating from canonical repo:**
- User says "check for updates" or "update the skill"
- SKILL.md shows skill is over a month old
- User wants new features from canonical repo

**Adding new content:**
- User creates a new agent
- User adds a new script or reference file
- Any change to the skill structure

**Why rebuild is needed:**
- Skills cannot be edited in place
- All changes require rebuilding via skill-creator
- User then replaces old skill with new via UI button

## Safety Principles

### Never Blind Overwrite
- Always show what's changing before rebuilding
- Always preserve user's custom content
- Always ask before removing anything

### Smart Merge Strategy
1. **New features** - Add from canonical (low risk)
2. **Modified system files** - Use canonical, show user what changed
3. **Hybrid files** - Merge intelligently (preserve user's additions)
4. **User files** - Always preserve (custom agents, custom patterns)

### The Rebuild Workflow
1. **Prepare** merged content in /tmp directory
2. **Validate** merge preserved customizations
3. **Use skill-creator** to rebuild skill package
4. **User replaces** via "Copy to your skills" button

**Critical:** You prepare and build, user clicks the button to replace.

---

## Quick Reference

### Fetching from GitHub

```bash
# List repo structure
curl -sL "https://github.com/USER/REPO/tree/BRANCH/PATH" | grep -o 'PATH/[^"]*' | sort -u

# Fetch file content (to stdout)
bash scripts/fetch-github-file.sh USER/REPO BRANCH path/to/file.md

# Fetch file content (to file)
bash scripts/fetch-github-file.sh USER/REPO BRANCH path/to/file.md /output/path.md
```

### Complete Update Workflow

```
1. Fetch canonical files to /tmp/canonical-synapse/
2. Check references/changelog.md for what changed
3. Copy user's custom agents to /tmp/canonical-synapse/agents/
4. Copy user's memory/ store across UNCHANGED (memory.json + longterm.db) — never the canonical seed
5. Merge SKILL.md Global Learned Patterns (user + canonical)
6. cd /tmp/canonical-synapse && bash scripts/rebuild-index.sh
7. Use skill-creator on /tmp/canonical-synapse/
8. Instruct user to click "Copy to your skills" to replace
```

If the install had no `memory/` before, don't fetch the store — run `python3 scripts/memory.py read && python3 scripts/memory.py doctor` once to materialise an empty `memory.json` + `longterm.db` (the binary db is never fetched). See "Memory Store: Special Handling".

### Adding New Agent/Script (Also Requires Rebuild)

```
1. Create/modify files in current skill location
2. cd /mnt/skills/user/professor-synapse && bash scripts/rebuild-index.sh
3. Use skill-creator on /mnt/skills/user/professor-synapse/
4. Instruct user to click "Copy to your skills" to replace
```

**Key Principle:** Any structural change = rebuild with skill-creator + user replaces via button.

**Blocked domains (do not attempt):**
- `api.github.com`
- `raw.githubusercontent.com`
- `cdn.jsdelivr.net`
- `raw.githack.com`

---

## Dependencies

The fetch scripts require:
- `curl` (standard on most systems)
- `python3`
- `html2text` Python package (auto-installed if missing)

To manually install html2text:
```bash
pip install html2text --break-system-packages
```