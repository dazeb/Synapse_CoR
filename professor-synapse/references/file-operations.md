# File Operations Reference

This skill can read and write files within its own directory structure. Use these operations to save new agents and record learned patterns.

## Skill Directory

The skill lives at: `/mnt/skills/user/professor-synapse/`

```
professor-synapse/
├── SKILL.md                 # Main identity (read-only in normal use)
├── agents/
│   ├── INDEX.md             # Auto-generated agent registry (rebuild with script)
│   └── [domain]-[specialty].md  # Agent files with frontmatter
├── references/
│   ├── learned-patterns.md  # Patterns & anti-patterns (UPDATE with learnings)
│   ├── agent-template.md    # Template for new agents (read-only reference)
│   ├── domain-expertise.md  # Domain mappings (UPDATE with new domains)
│   └── file-operations.md   # This file
└── scripts/
    └── rebuild-index.sh     # Regenerates agents/INDEX.md from frontmatter
```

## Available Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `view` | Read file contents | `path`, optionally line range |
| `create_file` | Create a new file | `path`, `file_text`, `description` |
| `str_replace` | Edit existing file | `path`, `old_str`, `new_str` |
| `bash_tool` | Run shell commands | `command` |

## How to Save a New Agent

### Step 1: Create the agent file

Use `create_file` tool:
- **path**: `/mnt/skills/user/professor-synapse/agents/[domain]-[specialty].md`
- **file_text**: The agent content following the template structure
- **description**: "Creating new [Title] agent"

Example:
```
path: /mnt/skills/user/professor-synapse/agents/python-async-expert.md
file_text: [agent content here]
description: Creating new Python Async Expert agent
```

### Step 2: Rebuild the Index

Run the rebuild script to update `agents/INDEX.md`:

```bash
bash scripts/rebuild-index.sh
```

### Step 3: Verify

Use `view` or `bash_tool` with `ls -la` to confirm the file was created.

## How to Update Learned Patterns

When a pattern emerges from successful interactions:

### Step 1: Read Current File
Use `view` to read current `references/learned-patterns.md`

### Step 2: Make the Edit
Use `str_replace` to add the new pattern:

```
old_str: [last line of existing pattern section]

new_str: [last line of existing pattern section]

### [New Pattern Name]
**Triggers**: [keywords, user level, task type]
...
```

Follow the template format already in the file.

### Step 3: Package the Skill
**Claude Desktop cannot edit skills in place.** After ANY file change, complete the packaging workflow:

```bash
# Rebuild index (in case agents were also modified)
cd /mnt/skills/user/professor-synapse && bash scripts/rebuild-index.sh

# Package skill
python3 /mnt/skills/examples/skill-creator/scripts/package_skill.py /mnt/skills/user/professor-synapse /home/claude/

# Copy to outputs
cp /home/claude/professor-synapse.skill /mnt/user-data/outputs/
```

### Step 4: Present to User
```
present_files → professor-synapse.skill
```

The user will see "Copy to your skills" button to install the updated skill.

**If you skip the packaging steps, the learned pattern will NOT persist when the user invokes Professor Synapse again.**

## Alternative: Using bash_tool

You can also use `bash_tool` for file operations:

```bash
# List available agents (the filesystem IS the index)
ls /mnt/skills/user/professor-synapse/agents/

# Create a file
echo "content" > /mnt/skills/user/professor-synapse/agents/python-async-expert.md

# View file contents
cat /mnt/skills/user/professor-synapse/agents/domain-researcher.md
```

## Best Practices

- **Always verify** after creating/updating files using `view` or `ls`
- **Use descriptive filenames** - e.g., `python-async-expert.md`
- **Include frontmatter** - every agent needs `name`, `emoji`, `description`, `triggers` (see `agent-template.md`)
- **Rebuild index after adding agents** - run `bash scripts/rebuild-index.sh`
- **For str_replace**: The `old_str` must be unique in the file. Include surrounding context if needed
- **Read before editing** - use `view` first to see current content and find the right insertion point

## Shell Compatibility Note

When writing bash commands, avoid brace expansion (e.g., `{a,b,c}`). Instead, use separate commands or list arguments explicitly. The execution environment may not support all interactive Bash features.
