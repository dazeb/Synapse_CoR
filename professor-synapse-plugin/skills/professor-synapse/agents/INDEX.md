# Agent Index

Built-in agents shipped with the plugin. Your own agents live in the plugin's
**data** dir and are merged in automatically — run `summon.py --list` for the
full, always-current roster (built-in + yours).

## Available Agents

| Agent | Emoji | Description | Triggers |
|-------|-------|-------------|----------|
| [domain-researcher](domain-researcher.md) | 🔎 | Research agent summoned before creating new domain experts. Browses web to gather best practices, frameworks, and terminology. | research, create agent, new domain, unfamiliar topic |
| [memory-agent](memory-agent.md) | 🧠 | Manages Professor Synapse's shared, agent-tagged memory: recall, capture, cleanup, and filtering by agent | remember, recall, what do you know, what do you remember, memory, forget this, what did the agent do, my context, who am i, update memory |
