# Skill Rebuild Protocol

## Purpose

After making local changes to the Professor Synapse skill (adding agents, modifying scripts, updating references), you must rebuild the entire skill using skill-creator and have the user replace it.

**Critical Understanding:** Skills cannot be edited in place. ANY structural change requires a complete rebuild.

---

## When to Use This Protocol

Use this when the user has made **local changes** to the skill:

**Common scenarios:**
- Created a new agent
- Added a new script
- Modified a reference file
- Updated learned-patterns.md
- Changed SKILL.md
- Any other structural change

**Not for GitHub updates:** If updating from the canonical repository, use `update-protocol.md` instead.

---

## The Rebuild Process

### Step 1: Validate Local Changes

Verify what changed:

```bash
# From skill directory
cd /mnt/skills/user/professor-synapse

# Check for new/modified files
ls -la agents/
ls -la references/
ls -la scripts/
```

Show user what will be included in the rebuild:
```
🧙🏾‍♂️: "I see you've added/modified:
- agents/your-new-agent.md (new)
- learned-patterns.md (modified)

I'll rebuild the skill to include these changes."
```

### Step 2: Rebuild Agent Index

**IMPORTANT:** Always rebuild the index before packaging:

```bash
cd /mnt/skills/user/professor-synapse
bash scripts/rebuild-index.sh
```

This ensures `agents/INDEX.md` includes all agents with correct frontmatter.

### Step 3: Use skill-creator

Use the skill-creator capability to rebuild the skill:

```
🧙🏾‍♂️: "Rebuilding the Professor Synapse skill with your changes..."

[Use skill-creator tool on /mnt/skills/user/professor-synapse/]
```

The skill-creator will:
1. Package the directory as a skill zip
2. Validate the structure (frontmatter, required files)
3. Generate skill preview
4. Make it available for installation

### Step 4: User Replaces Skill

Once skill-creator finishes, instruct the user:

```
🧙🏾‍♂️: "✅ Skill rebuilt successfully!

To replace your current Professor Synapse skill with this updated version:

1. You should see a skill preview/confirmation below
2. Click the 'Copy to your skills' button
3. This will REPLACE your existing Professor Synapse skill
4. Your changes are now part of the skill

Changes included in this rebuild:
- [List what was added/modified]

Ready to replace your skill?"
```

**Important:** The user must click the button—you cannot do this programmatically.

---

## Quick Reference

### Complete Rebuild Workflow

```bash
# 1. Navigate to skill directory
cd /mnt/skills/user/professor-synapse

# 2. Verify changes
ls -la agents/ references/ scripts/

# 3. Rebuild index
bash scripts/rebuild-index.sh

# 4. Use skill-creator
[Use skill-creator tool on current directory]

# 5. Instruct user to click "Copy to your skills"
```

### Common Rebuild Triggers

| Trigger | Why Rebuild Needed |
|---------|-------------------|
| New agent created | INDEX.md needs update, skill structure changed |
| Agent modified | Skill package needs to include latest version |
| Script added/modified | Skill structure changed |
| Reference updated | Documentation changed |
| learned-patterns.md updated | Accumulated knowledge changed |
| SKILL.md updated | Core behavior changed |

**Key Principle:** Any file change = rebuild with skill-creator + user replaces via button.

---

## Example: Adding a New Agent

```
User: "I created a new Python expert agent"

🧙🏾‍♂️: "Great! I see agents/python-expert.md in your skill directory.
To make it available when you invoke Professor Synapse, I need to rebuild the skill.

Let me rebuild the index and package the updated skill..."

[Runs rebuild-index.sh]
[Uses skill-creator]

🧙🏾‍♂️: "✅ Rebuilt!

Your new agent is included:
- agents/python-expert.md (Python expertise with async patterns)

Click 'Copy to your skills' below to replace your Professor Synapse skill with this updated version.
Then you'll be able to summon the Python expert!"
```

---

## Troubleshooting

### skill-creator fails validation

**Symptom:** skill-creator reports missing frontmatter or invalid structure

**Fix:**
1. Check agent frontmatter (all agents need name, emoji, description, triggers)
2. Verify SKILL.md has proper frontmatter
3. Run `bash scripts/rebuild-index.sh` to regenerate INDEX.md
4. Try skill-creator again

### User's button doesn't appear

**Symptom:** User doesn't see "Copy to your skills" button

**Possible causes:**
- skill-creator didn't finish successfully
- Skill validation failed
- Network/UI issue

**Fix:** Check skill-creator output for errors, retry if needed

### Changes not reflected after replace

**Symptom:** User replaced skill but doesn't see changes

**Possible causes:**
- Old skill cached
- Didn't click replace button
- Replace failed silently

**Fix:** Ask user to refresh/reload, or try rebuild again

---

## Notes

- **Rebuild is fast** - Usually completes in seconds
- **Always rebuild index first** - Ensures agents are registered correctly
- **User controls when to replace** - They click the button when ready
- **No data loss** - Rebuilding doesn't delete user customizations
- **Can rebuild multiple times** - If something's wrong, just rebuild again

**Remember:** This is just for local changes. For GitHub updates, use `update-protocol.md`.
