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

### What Works
Use `bash_tool` with `curl` to fetch GitHub tree pages and parse the HTML:

```bash
# Fetch folder listing and extract file paths
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse" | grep -o 'professor-synapse/[^"]*' | sort -u

# Fetch subfolder contents (agents, references, scripts)
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse/agents" | grep -o 'professor-synapse/agents/[^"]*\.md' | sort -u

curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse/references" | grep -o 'professor-synapse/references/[^"]*\.md' | sort -u

curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse/scripts" | grep -o 'professor-synapse/scripts/[^"]*' | sort -u
```

### What Does NOT Work
- `api.github.com` - Blocked (403 host_not_allowed)
- `raw.githubusercontent.com` - Blocked (403 host_not_allowed)
- `web_search` - Often doesn't find specific repo folders/files
- `web_fetch` - Requires URLs to be provided by user or appear in search results first

### Fetching File Contents
To get actual file contents fetch the blob page HTML and extract content (less reliable, content is embedded in JS):
```bash
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/blob/main/professor-synapse/SKILL.md"
# Then parse the HTML for file content (complex, may require regex)
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

Use bash to discover what files exist in the canonical repo:

```bash
# Get top-level structure
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse" | grep -o 'professor-synapse/[^"]*' | sort -u

# Get agents
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse/agents" | grep -o 'professor-synapse/agents/[^"]*\.md' | sort -u

# Get references
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse/references" | grep -o 'professor-synapse/references/[^"]*\.md' | sort -u

# Get scripts
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/tree/main/professor-synapse/scripts" | grep -o 'professor-synapse/scripts/[^"]*' | sort -u
```

### Step 2: Compare With Local

Use `view` tool to list local skill contents:

```bash
view /mnt/skills/user/professor-synapse
```

Compare the two lists to identify:
- **New files** in canonical (not in local)
- **Missing files** in canonical (user's custom content)
- **Shared files** (potentially modified)

### Step 3: Analyze Changes

Create a summary for the user:

```
🧙🏾‍♂️: "I've checked for updates. Here's what I found:

**Canonical Repo Structure:**
- SKILL.md
- agents/domain-researcher.md, INDEX.md
- references/[list files]
- scripts/rebuild-index.sh

**New Files Available:**
- references/convener-protocol.md (new capability)
- references/update-protocol.md (this protocol)

**Your Custom Content (will be preserved):**
- agents/your-custom-agent.md
- [other custom agents]

**Potentially Modified (need file contents to compare):**
- SKILL.md
- agents/domain-researcher.md

Would you like me to fetch the contents of the new/modified files?
To do this, please provide raw URLs or confirm you want me to attempt HTML scraping."
```

### Step 4: Fetch File Contents (When Needed)

**For new files:** Use bash to fetch and parse:
```bash
curl -sL "https://github.com/ProfSynapse/Professor-Synapse/blob/main/professor-synapse/references/convener-protocol.md" > /tmp/page.html
# Content is in the HTML but embedded in React/JS - may need user assistance
```

### Step 5: Apply Updates Safely

**For NEW files:**
- ✅ Safe to add directly
- Create the file with content from repo

**For MODIFIED system files (SKILL.md, references/protocols):**
1. Show the user a summary of what changed (not full diff unless requested)
2. Recommend applying the update
3. If user approves, apply the changes

**For HYBRID files (learned-patterns.md):**
1. Identify what's new in the canonical version (new system patterns)
2. Identify what the user has added locally (their custom patterns)
3. Merge: Keep user's patterns + add new system patterns
4. Show user what was merged

**For USER CONTENT (agents/*):**
- ❌ NEVER overwrite
- If a system agent like `domain-researcher.md` was updated, offer to update
- For user's custom agents, skip entirely

### Step 6: Rebuild Index

After applying updates:
```bash
cd /mnt/skills/user/professor-synapse && bash scripts/rebuild-index.sh
```

This regenerates `agents/INDEX.md` with all current agents (system + user's custom ones).

### Step 7: Test & Confirm

```
🧙🏾‍♂️: "Updates applied! Changes:
- [List what was updated]

Your customizations preserved:
- [List user's custom content]

Try invoking the skill to confirm everything works."
```

---

## Safety Principles

### Never Blind Overwrite
- Always show what's changing
- Always preserve user's custom content
- Always ask before deleting anything

### Smart Merge Strategy
1. **New features** → Add them (low risk)
2. **Modified system files** → Show diff, recommend update
3. **Hybrid files** → Merge intelligently (preserve user's additions)
4. **User files** → Never touch (except system agents with permission)

### Conflict Resolution

If a file has BOTH system changes AND user customizations:

**Option 1: Side-by-side** (safest)
- Save canonical version as `[file].canonical`
- Keep user's version as `[file]`
- Show user the differences
- Let user manually merge if they want

**Option 2: Smart merge** (if possible)
- Identify non-overlapping changes
- Merge both sets of changes
- Show user what was merged

**When in doubt:** Option 1 (side-by-side). Better to be safe.

---

## Quick Reference: Working Commands

```bash
# List folder structure
curl -sL "https://github.com/[USER]/[REPO]/tree/main/[PATH]" | grep -o '[PATH]/[^"]*' | sort -u

# List .md files in a folder
curl -sL "https://github.com/[USER]/[REPO]/tree/main/[PATH]" | grep -o '[PATH]/[^"]*\.md' | sort -u

# Test if github.com is accessible
curl -sI "https://github.com" | head -3
```

**Blocked domains (do not attempt):**
- `api.github.com`
- `raw.githubusercontent.com`
```