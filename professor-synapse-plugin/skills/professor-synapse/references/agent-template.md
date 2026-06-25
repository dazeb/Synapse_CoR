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

## Learned Patterns

### Effective Patterns
<!-- Domain-specific patterns that work well for this agent. Add entries as you learn. -->

### Anti-Patterns
<!-- Domain-specific mistakes to avoid for this agent. Add entries as you learn. -->
```

## Using Research Output

When creating a new agent, first summon 🔎 Domain Researcher. Use their structured output to fill in:
- **CONTEXT**: Informed by "Common User Needs" research
- **INSTRUCTIONS**: Based on "Key Frameworks/Methodologies"
- **GUIDELINES**: Incorporate "Anti-Patterns to Avoid" and domain vocabulary
- **Emoji/Title**: Use "Recommended Agent Configuration" suggestions

## Supporting files (Optional) — scripts, references, templates, protocols

An agent can lean on supporting files instead of cramming everything into its
instructions. Your data dir mirrors the core layout, with a writable home for
each category:

| Put it in `<data_root>/…` | For | Cite it in the agent as |
|---|---|---|
| `scripts/` | a repeated operation (rebuild a cache, fetch data, transform files) — see `references/scripts-protocol.md` | `` `scripts/[name].sh` `` / `` `scripts/[name].py` `` |
| `references/` | reference material the agent reads | `` `references/[name].md` `` |
| `templates/` | a reusable template the agent fills in | `` `templates/[name].md` `` |
| `protocols/` | a step-by-step procedure the agent follows | `` `protocols/[name].md` `` |

**The rule that wires it up:** save the file in the matching subdir, then **cite
its relative path in backticks** somewhere in the agent body. On the next summon,
`summon.py` surfaces it in the boot package as an **absolute path** (resolved
your-data-first, then core), so it loads or runs from any working directory — no
packaging step. For scripts, also add a **Scripts** section so the invocation is
obvious:

```markdown
## Scripts

| Script | Purpose | Invoke |
|--------|---------|--------|
| `scripts/[name].sh` | What it does | `bash scripts/[name].sh --help` |
```

A user file shadows a shipped core file of the same relative path, exactly like
user agents override built-in agents.

## After Creation

> Your agents (and their supporting files) live in the plugin's writable **data**
> dir, separate from the read-only core. Saving the file there makes it available
> on the next `summon.py` run — agents are merged into the roster, cited
> supporting files are surfaced.

### Step 1: Save the Agent
Create the file in the data agents dir, named `[domain]-[specialty].md`:
```
<data_root>/agents/ml-business-translator.md
```
Find `<data_root>` by running `python3 scripts/_pluginpaths.py` (or just save it
where `summon.py --list` already shows your other agents). Example: an ML expert
for business users → `ml-business-translator.md`.

### Step 2: (Optional) Refresh the human-readable index
Routing already picks the agent up via `summon.py --list`. If you also want the
merged `INDEX.md` regenerated, run:
```bash
bash scripts/rebuild-index.sh
```
That ensures a `Learned Patterns` section on each user agent and writes the
merged index into the data dir. It is a convenience, not a requirement.
