# Update Protocol: Safely Merging Skill Updates

## Purpose

This protocol allows users to pull updates to the Professor Synapse skill **without overwriting their customizations** (custom agents, learned patterns, local modifications).

You are performing a **smart merge**, not a blind overwrite.

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
3. Extract the `richText` field (rendered HTML) or `rawLines` (for non-markdown)
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
| **System Core** | `SKILL.md`, `scripts/*` | Show diff, recommend applying updates |
| **Reference Protocols** | `references/*.md` (except learned-patterns) | Show diff, offer to apply |
| **Template** | `references/agent-template.md` | Show diff, usually safe to update |
| **Hybrid** | `references/learned-patterns.md` | Smart merge (preserve user's patterns, add new system patterns) |
| **User Content** | `agents/*` (except domain-researcher) | NEVER overwrite - user's custom agents |
| **System Agent** | `agents/domain-researcher.md` | Show diff, offer to update |
| **Auto-generated** | `agents/INDEX.md` | Don't update directly - regenerated from agents |

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

### Step 3: Fetch and Compare Files

For each file that might have updates:

```bash
# Fetch canonical version to temp location
bash scripts/fetch-github-file.sh ProfSynapse/Professor-Synapse main professor-synapse/SKILL.md > /tmp/canonical-SKILL.md

# Compare with local
diff /mnt/skills/user/professor-synapse/SKILL.md /tmp/canonical-SKILL.md
```

### Step 4: Apply Updates Safely

**For NEW files:**
```bash
bash scripts/fetch-github-file.sh ProfSynapse/Professor-Synapse main professor-synapse/references/new-file.md > /mnt/skills/user/professor-synapse/references/new-file.md
```

**For MODIFIED system files:**
1. Show user what changed (summary, not full diff unless requested)
2. Recommend applying if changes look beneficial
3. If user approves, overwrite with canonical version

**For HYBRID files (learned-patterns.md):**
1. Fetch canonical version to /tmp
2. Identify user's custom patterns (content not in canonical)
3. Merge: canonical structure + user's custom additions
4. Show user what was merged
5. Apply the merged version

**For USER CONTENT (custom agents):**
- Never overwrite without explicit permission
- If user created agents that don't exist in canonical, always preserve them

### Step 5: Rebuild Index

After applying updates:

```bash
cd /mnt/skills/user/professor-synapse && bash scripts/rebuild-index.sh
```

This regenerates `agents/INDEX.md` with all current agents (system + user's custom ones).

### Step 6: Confirm

Report what was updated and what was preserved:

```
🧙🏾‍♂️: "Updates applied! Changes:
- Added: references/new-protocol.md
- Updated: SKILL.md (added new workflow step)
- Updated: scripts/rebuild-index.sh (bug fix)

Your customizations preserved:
- agents/your-custom-agent.md
- learned-patterns.md (your patterns kept, new system patterns added)

Try invoking the skill to confirm everything works."
```

---

## Safety Principles

### Never Blind Overwrite
- Always show what's changing before applying
- Always preserve user's custom content
- Always ask before deleting anything

### Smart Merge Strategy
1. **New features** - Add them (low risk)
2. **Modified system files** - Show diff, recommend update
3. **Hybrid files** - Merge intelligently (preserve user's additions)
4. **User files** - Never touch (except system agents with permission)

### Conflict Resolution

If a file has BOTH system changes AND user customizations:

**Option 1: Side-by-side (safest)**
- Save canonical version as `[file].canonical`
- Keep user's version as `[file]`
- Show user the differences
- Let user manually merge if they want

**Option 2: Smart merge (if possible)**
- Identify non-overlapping changes
- Merge both sets of changes
- Show user what was merged

**When in doubt:** Option 1 (side-by-side). Better to be safe.

---

## Quick Reference

```bash
# List repo structure
curl -sL "https://github.com/USER/REPO/tree/BRANCH/PATH" | grep -o 'PATH/[^"]*' | sort -u

# Fetch file content (to stdout)
bash scripts/fetch-github-file.sh USER/REPO BRANCH path/to/file.md

# Fetch file content (to specific file)
bash scripts/fetch-github-file.sh USER/REPO BRANCH path/to/file.md /output/path.md

# Rebuild agent index after changes
bash scripts/rebuild-index.sh
```

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