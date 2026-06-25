# Scripts Protocol

Scripts are standalone, self-documenting CLI tools. Agents don't need to read source code — they run `script --help` to learn usage, then invoke as needed.

## Philosophy

- **Code lives in `scripts/`** — separate from documentation
- **CLI-first design** — every script explains itself via `--help`
- **Agents reference, not embed** — agent files point to scripts; they don't duplicate logic

## Where scripts live (plugin)

Two locations, mirroring the agents split:

- **Core scripts** ship with the plugin (`<core>/scripts/`: `summon.py`,
  `memory.py`, `rebuild-index.sh`, `_pluginpaths.py`). Read-only — they're
  **replaced on every plugin update**, so don't edit them; your changes would be
  lost.
- **Your scripts** go in the writable **data** dir: `<data_root>/scripts/`. These
  **survive updates**. Find `<data_root>` with `python3 scripts/_pluginpaths.py`.

When an agent cites `` `scripts/[name].sh` ``, `summon.py` resolves it
**data-first, then core**, and surfaces the **absolute** path in the boot
package — so a user script shadows a core script of the same name, and either
runs from any working directory.

## When to Create a Script

Create a script when an agent needs to perform the same operation repeatedly:
- Rebuilding indexes or caches
- Fetching or syncing external data
- Packaging or transforming files
- Any multi-step operation worth automating

## Required Interface

Every script MUST support a `--help` / `-h` flag that prints:

1. **What it does** — one-line description
2. **Usage** — syntax with argument placeholders
3. **Arguments** — each argument described
4. **Examples** — at least two concrete examples
5. **Dependencies** — any required tools

### Shell Script Template

```bash
#!/bin/bash
# [one-line description]

show_help() {
    cat << 'EOF'
USAGE
  script-name.sh [options] <required-arg> [optional-arg]

DESCRIPTION
  What the script does in 1-2 sentences.

ARGUMENTS
  <required-arg>   Description of required argument
  [optional-arg]   Description of optional argument (default: value)

OPTIONS
  -h, --help       Show this help message

EXAMPLES
  script-name.sh foo
  script-name.sh foo bar

DEPENDENCIES
  tool1, tool2
EOF
}

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi
```

### Python Script Template

```python
#!/usr/bin/env python3
"""one-line description"""

import argparse

def main():
    parser = argparse.ArgumentParser(description="What the script does.")
    parser.add_argument("required_arg", help="Description")
    parser.add_argument("optional_arg", nargs="?", default="value", help="Description")
    args = parser.parse_args()
    # ...

if __name__ == "__main__":
    main()
```

Python's `argparse` generates `--help` automatically — no extra work needed.

## How Agents Reference Scripts

In an agent's definition, add a **Scripts** section listing scripts the agent may need:

```markdown
## Scripts

| Script | Purpose | Invoke |
|--------|---------|--------|
| `scripts/rebuild-index.sh` | Regenerate agent index | `bash scripts/rebuild-index.sh --help` |
```

Agents should run `--help` first if uncertain about arguments or options.

## Existing core scripts (shipped, read-only)

| Script | Purpose | Help |
|--------|---------|------|
| `scripts/summon.py` | Assemble an agent boot package (persona + recalled memory + loadable resources) | `python3 scripts/summon.py --help` |
| `scripts/memory.py` | Shared agent-tagged memory store (working + long-term) | `python3 scripts/memory.py --help` |
| `scripts/rebuild-index.sh` | Rebuild the merged `agents/INDEX.md` from agent frontmatter | `bash scripts/rebuild-index.sh --help` |
| `scripts/_pluginpaths.py` | Resolve the writable data root (`python3 scripts/_pluginpaths.py` prints it) | — |

(Updating is handled by Claude Code: `/plugin update professor-synapse`. There is
no `update.sh`.)

## Adding a New Script (yours)

1. Create `<data_root>/scripts/[name].sh` (or `.py`) — **not** in core, which is
   overwritten on update. (`python3 scripts/_pluginpaths.py` prints `<data_root>`.)
2. Implement `--help` following the template above.
3. In the agent that uses it, add a **Scripts** section and cite
   `` `scripts/[name].sh` `` in the body so `summon.py` surfaces it (absolute path,
   data-first).

No need to update SKILL.md or this file for your own scripts — citation is what
wires them in.
