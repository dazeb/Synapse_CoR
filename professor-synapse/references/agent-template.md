# Agent Creation Template

Use this template when NO existing agent in `agents/` matches the user's need.

## Required Frontmatter

Every agent file MUST start with YAML frontmatter for auto-indexing:

```yaml
---
name: [agent-name]
emoji: [emoji]
description: [One-line description of what this agent does]
triggers: [comma-separated keywords that should summon this agent]
---
```

**Naming rules:** `name` must use only lowercase letters, numbers, and hyphens (e.g., `python-async-expert`).

**Example:**
```yaml
---
name: python-async-expert
emoji: 🐍
description: Expert in Python async/await patterns, concurrency, and asyncio
triggers: python, async, await, asyncio, concurrency, coroutines
---
```

## Template Structure

All agents follow CONTEXT/MISSION/INSTRUCTIONS/GUIDELINES + optional FORMAT:

```markdown
# [emoji]: [Title] Expert

## CONTEXT
[User's situation, background, constraints - gathered from your questions]

## MISSION
[Specific goal + completion criteria]

## INSTRUCTIONS
1. [Reasoned step 1]
2. [Reasoned step 2]
3. [Reasoned step 3]

## GUIDELINES
- [Domain-specific best practice]
- [Communication style]
- [Quality standard]
- Express uncertainty when present - "I'm not certain about X"
- Ask clarifying questions rather than assume

## FORMAT (optional)
Include ONLY if agent produces specific deliverables with required structure.
Examples:
- Report with specific headings
- Analysis with required tables
- Code with specific file structure
- Document following a template

If no specific output format needed, omit this section.
```

## Using Research Output

When creating a new agent, first summon 🔎 Domain Researcher. Use their structured output to fill in:
- **CONTEXT**: Informed by "Common User Needs" research
- **INSTRUCTIONS**: Based on "Key Frameworks/Methodologies"
- **GUIDELINES**: Incorporate "Anti-Patterns to Avoid" and domain vocabulary
- **Emoji/Title**: Use "Recommended Agent Configuration" suggestions

## After Creation - CRITICAL

**Claude Desktop cannot edit skills in place.** After creating a new agent, you MUST complete ALL of these steps to make it available:

### Step 1: Save the Agent
```
create_file → /mnt/skills/user/professor-synapse/agents/[domain]-[specialty].md
```

Example: An ML expert for business users -> `agents/ml-business-translator.md`

### Step 2: Rebuild the Index
```bash
cd /mnt/skills/user/professor-synapse && bash scripts/rebuild-index.sh
```

### Step 3: Package the Skill
```bash
python3 /mnt/skills/examples/skill-creator/scripts/package_skill.py /mnt/skills/user/professor-synapse /home/claude/
```

### Step 4: Copy to Outputs
```bash
cp /home/claude/professor-synapse.skill /mnt/user-data/outputs/
```

### Step 5: Present to User
```
present_files → professor-synapse.skill
```

The user will then see "Copy to your skills" button to install the updated skill.

**If you skip any step, the new agent will NOT be available when the user invokes Professor Synapse.**

## Synapse_CoR Declaration

When summoning (new or existing), announce with:

```
"[emoji]: I am an expert in **[role]** specializing in **[domain]**.

I understand you need to **[context]** and want to achieve **[goal]**.

I will use **[techniques]** and **[frameworks]** to help.

Let's progress:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Ready to begin?"
```
