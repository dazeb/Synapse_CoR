#!/usr/bin/env python3
"""SessionStart hook: prepare the data dir and inject routing context.

Two jobs at session start:
  1. Ensure the writable data dirs exist: <data_root>/agents and
     <data_root>/memory. summon.py/memory.py also create these on demand, but
     pre-creating means a brand-new install has somewhere for the user's first
     agent and first memory to land without a race.
  2. Inject context so the model knows the ABSOLUTE path to summon.py. This is
     essential: model-invoked Bash does NOT receive ${CLAUDE_PLUGIN_ROOT}, so
     without this the model cannot reliably locate the script to run it. We emit
     the resolved path plus the one-line protocol.

SessionStart stdout is added to the model's context. We use the structured
hookSpecificOutput.additionalContext form.

Fail-open: any error exits 0 with no output.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import _hookpaths
except Exception:
    _hookpaths = None


def main() -> int:
    # Consume stdin if present (SessionStart provides JSON); ignore parse errors.
    try:
        sys.stdin.read()
    except Exception:
        pass

    if _hookpaths is None:
        return 0
    try:
        data = _hookpaths.data_root()
        skill = _hookpaths.skill_root()
        summon = _hookpaths.summon_path()
    except Exception:
        return 0

    # 1. Ensure writable dirs exist.
    try:
        (data / "agents").mkdir(parents=True, exist_ok=True)
        (data / "memory").mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # 2. Inject routing context with absolute, runnable paths.
    context = (
        "Professor Synapse plugin is active. Route every task through Professor "
        "Synapse: summon the owning agent BEFORE task work (recall, reading task "
        "files, planning, editing), then become it and speak with its emoji.\n\n"
        f"SKILL: {skill / 'SKILL.md'}\n"
        f"Browse the full roster (built-in + your agents):\n"
        f'  python3 "{summon}" --list\n'
        f"Summon an agent (this also recalls its memory):\n"
        f'  python3 "{summon}" "<agent or task phrase>"\n'
        f"If no agent fits, record the decision:\n"
        f'  python3 "{summon}" --self --reason "why none fits"\n\n'
        "Note: ${CLAUDE_PLUGIN_ROOT}/${CLAUDE_PLUGIN_DATA} are NOT visible to the "
        "Bash you run — use the absolute paths above. Your own agents and memory "
        f"persist under {data} and survive plugin updates."
    )
    out = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
