# Professor Synapse — Claude Code plugin

Professor Synapse is a **router**: instead of pretending to know everything, it
summons the right expert agent for the task, hands it persistent memory, and
keeps the conversation on-persona. This plugin packages Professor for Claude Code
so you can install it once and get updates without ever losing the agents or
memory you build on top of it.

## What you get

- **Professor Synapse** 🧙🏾‍♂️ — the orchestrator/router persona.
- **Built-in agents** — `domain-researcher` 🔎 (researches a domain before you
  spin up a new expert) and `memory-agent` 🧠 (owns the durable memory store).
- **Persistent, agent-tagged memory** — ranked recall, a knowledge graph, and
  per-agent scoping (`scripts/memory.py`).
- **Three hooks** that enforce the protocol:
  - `summon-gate` (PreToolUse) — blocks file edits and memory writes until you
    summon an owning agent; memory **writes** additionally require the
    memory-agent.
  - `persona-guard` (Stop) — nudges you back into character if a reply drops the
    active agent's emoji prefix.
  - `memory-nudge` (Stop) — reminds you to ask about saving after a stretch of
    work with no memory activity.

## Install

```bash
# Add this repo as a marketplace, then install the plugin:
/plugin marketplace add profsynapse/professor-synapse
/plugin install professor-synapse@professor-synapse
```

(Or from a local checkout: `/plugin marketplace add /path/to/Professor-Synapse`.)

Restart the session (or start a new one) so the `SessionStart` bootstrap runs.
It creates your data dirs and injects the absolute path to `summon.py`.

## How it works — core vs. your data

The plugin keeps **two** locations strictly separate:

| | Location | Lifecycle |
|---|---|---|
| **Core** (this plugin) | `…/plugins/cache/<marketplace>/professor-synapse/<version>/` | Replaced wholesale on every update |
| **Your data** | `…/plugins/data/professor-synapse-<marketplace>/` | Persists across updates; removed only on uninstall |

Your **own agents** (`<data>/agents/`), the **memory store** (`<data>/memory/`),
and the summon-gate marker all live in the data dir. So when the author ships a
new version and you run `/plugin update professor-synapse`, the core (SKILL,
scripts, built-in agents) refreshes and **everything you created is untouched**.

> **Why the scripts derive their own paths:** Claude Code injects
> `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}` into *hook* execution but
> **not** into the Bash the model runs. So `summon.py`/`memory.py` derive the
> data dir from their own install path (`scripts/_pluginpaths.py`), while the
> hooks read the env vars. The `SessionStart` hook injects the absolute
> `summon.py` path into context so the model always knows where to call it.

## Everyday use

```bash
# Browse every agent (built-in + yours):
python3 "<plugin>/scripts/summon.py" --list

# Summon one (this also recalls its memory):
python3 "<plugin>/scripts/summon.py" "<agent or task phrase>"

# Create your own agent: drop a markdown file in <data>/agents/ — it's live on
# the next summon. No packaging or reinstall. (See references/agent-template.md.)
```

`<plugin>` is the install dir; the `SessionStart` hook prints the absolute path,
or run `python3 scripts/_pluginpaths.py` to find your data dir.

## Update

```bash
/plugin update professor-synapse
```

Core updates; your agents and memory survive. Verify an install or update with
`references/self-check.md`.

## License

MIT.
