# File Operations Reference

This skill can read and write files within its own directory structure. Use these operations to save new agents and record learned patterns.

## Skill Directory

The skill lives at: `/mnt/skills/user/professor-synapse/`

```
professor-synapse/
├── SKILL.md                 # Main identity (read-only in normal use)
├── agents/
│   └── [domain]-[specialty].md  # Self-documenting filenames (use `ls` to discover)
└── references/
    ├── learned-patterns.md  # Patterns & anti-patterns (UPDATE with learnings)
    ├── agent-template.md    # Template for new agents (read-only reference)
    ├── domain-expertise.md  # Domain mappings (UPDATE with new domains)
    └── file-operations.md   # This file
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

### Step 2: Verify

Use `view` or `bash_tool` with `ls -la` to confirm the file was created.

## How to Update Learned Patterns

When a pattern emerges from successful interactions:

1. Use `view` to read current `references/learned-patterns.md`
2. Use `str_replace` to add the new pattern after an existing one:

```
old_str: [last line of existing pattern section]

new_str: [last line of existing pattern section]

### [New Pattern Name]
**Triggers**: [keywords, user level, task type]
...
```

3. Follow the template format already in the file

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
- **Use descriptive filenames** - the filename IS the discovery mechanism (e.g., `python-async-expert.md`)
- **For str_replace**: The `old_str` must be unique in the file. Include surrounding context if needed
- **Read before editing** - use `view` first to see current content and find the right insertion point
