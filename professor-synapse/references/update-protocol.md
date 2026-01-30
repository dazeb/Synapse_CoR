# Update Protocol: Safely Merging Skill Updates

## Purpose

This protocol allows users to pull updates to the Professor Synapse skill **without overwriting their customizations** (custom agents, learned patterns, local modifications).

You are performing a **smart merge**, not a blind overwrite.

---

## The Canonical Source

**GitHub Repository:** `https://github.com/profsynapse/Professor-Synapse`
**Skill Location:** `professor-synapse/` folder

When user invokes `/update` or says "update the skill", fetch the latest version from this source.

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

### Step 1: Fetch Latest Version

Use WebSearch or WebFetch to access the GitHub repo:

```
1. Search for "Professor-Synapse GitHub [user]" or navigate to known repo URL
2. Navigate to `professor-synapse/` folder
3. Fetch contents of the skill directory
```

**Note which files have changed** since user's last update (if possible, check git commit history or dates).

### Step 2: Analyze Changes

For each changed file, determine:
- **File category** (see table above)
- **Type of change**: New file, modified file, or deleted file
- **Risk level**: Will this conflict with user customizations?

Create a summary:
```
🧙🏾‍♂️: "I've checked for updates. Here's what changed:

**New Features:**
- references/convener-protocol.md (new capability)
- references/update-protocol.md (this protocol)

**Modified System Files:**
- SKILL.md (added convener mode to workflow)
- references/agent-template.md (clarified frontmatter rules)

**Your Custom Content (untouched):**
- agents/python-expert.md (your custom agent)
- learned-patterns.md (has your patterns)

Would you like me to apply these updates?"
```

### Step 3: Apply Updates Safely

**For NEW files:**
- ✅ Safe to add directly
- Create the file with content from repo

**For MODIFIED system files (SKILL.md, references/protocols):**
1. Show the user a summary of what changed (not full diff unless requested)
2. Recommend applying the update
3. If user approves, apply the changes

Example:
```
🧙🏾‍♂️: "SKILL.md was updated to:
- Add 'convener-protocol.md' to resources table
- Simplify workflow section
- Remove detailed convener instructions (now in protocol)

This looks safe - it's adding capabilities without removing anything. Apply?"
```

**For HYBRID files (learned-patterns.md):**
1. Identify what's new in the canonical version (new system patterns)
2. Identify what the user has added locally (their custom patterns)
3. Merge: Keep user's patterns + add new system patterns
4. Show user what was merged

Example:
```
🧙🏾‍♂️: "learned-patterns.md update:
- Canonical added: 'Technical Decision Debate' pattern
- You have: 3 custom patterns you've learned

I'll merge: keep your 3 patterns + add the new system pattern. Sound good?"
```

**For USER CONTENT (agents/*):**
- ❌ NEVER overwrite
- If a system agent like `domain-researcher.md` was updated, offer to update
- For user's custom agents, skip entirely

Example:
```
🧙🏾‍♂️: "Skipping your custom agents:
- agents/python-expert.md (yours)
- agents/ml-translator.md (yours)

System agent updated:
- agents/domain-researcher.md (Synapse team added web search capability)

Update domain-researcher? (Your custom agents are safe.)"
```

**For DELETED files:**
- ⚠️ Ask user before deleting anything
- Explain why it was removed

### Step 4: Rebuild Index

After applying updates:
```bash
bash scripts/rebuild-index.sh
```

This regenerates `agents/INDEX.md` with all current agents (system + user's custom ones).

### Step 5: Test & Confirm

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
- Save canonical version as `[file].new`
- Keep user's version as `[file]`
- Show user the differences
- Let user manually merge if they want

**Option 2: Smart merge** (if possible)
- Identify non-overlapping changes
- Merge both sets of changes
- Show user what was merged

**When in doubt:** Option 1 (side-by-side). Better to be safe.

---

## Example Update Session

```
User: "Update the Professor Synapse skill"

🧙🏾‍♂️: "I'll check for updates from the canonical repo..."

[Fetches from GitHub]

🧙🏾‍♂️: "Found updates! Here's what changed:

**New Capabilities:**
- references/convener-protocol.md - Multi-agent debate facilitation
- references/update-protocol.md - This update system

**System Updates:**
- SKILL.md - Added convener mode, simplified workflow
- references/agent-template.md - Clarified naming rules

**Your Custom Content (preserved):**
- agents/python-expert.md
- agents/data-analyst.md
- 4 custom patterns in learned-patterns.md

**Recommendation:** These updates add new features without removing anything. Safe to apply.

Proceed with update?"

User: "Yes"

🧙🏾‍♂️: "Applying updates..."

[Creates new files]
[Updates system files]
[Merges learned-patterns.md]
[Rebuilds INDEX.md]

🧙🏾‍♂️: "✅ Update complete!

**Added:**
- Convener protocol (load when you need multi-perspective debates)
- Update protocol (this!)

**Updated:**
- SKILL.md workflow section
- Agent template with naming rules

**Preserved:**
- All your custom agents
- Your learned patterns (merged with new system patterns)

Try using the skill - everything should work as before, plus new capabilities!"
```

---

## Edge Cases

### User Modified SKILL.md
If user has customized SKILL.md (added their own sections):
1. Detect the customizations (compare to last known system version)
2. Show canonical SKILL.md changes
3. Offer side-by-side: `SKILL.md` (user's) + `SKILL.md.new` (canonical)
4. User can manually merge if they want

### Conflicting Agent Names
If canonical adds `agents/python-expert.md` but user already has one:
1. Don't overwrite user's version
2. Save canonical as `agents/python-expert.canonical.md`
3. Notify user: "FYI: canonical added python-expert, saved as .canonical.md for reference"

### Git Repo Structure Changed
If the repo reorganizes structure:
1. Notify user: "⚠️ Major structure change detected"
2. Recommend manual review
3. Offer to apply only obviously safe changes (new files in new locations)

---

## Triggering Updates

User can trigger with:
- `/update` command
- "Update the Professor Synapse skill"
- "Check for skill updates"
- "Pull latest Professor Synapse version"

**Frequency:** Updates should be user-initiated, not automatic. Respect user's version control.

---

## After Updating

Suggest user test the skill:
```
🧙🏾‍♂️: "Test the updated skill by invoking it:
- Try summoning an agent (tests basic functionality)
- Try '/convene' if you want to test the new convener protocol
- Check that your custom agents still appear in INDEX.md

If anything seems broken, let me know!"
```
