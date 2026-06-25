#!/usr/bin/env python3
"""Shared path resolver for the Professor Synapse plugin hooks.

Hooks run in plugin hook context, where Claude Code DOES inject
${CLAUDE_PLUGIN_ROOT} (the install/cache dir) and ${CLAUDE_PLUGIN_DATA}
(the persistent data dir). That is the opposite of model-invoked Bash, which
sees neither — so the scripts (summon.py/memory.py) derive the data dir from
their own path, while these hooks can simply read the env vars, with the same
derivation as a fallback so a hook is never wrong about where state lives.

Everything here fails soft: callers treat a None/missing result as "allow".
Stdlib only. Lives beside the hooks so `import _hookpaths` works (the hook's
own directory is on sys.path[0] when run as a script).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SKILL_SUBPATH = ("skills", "professor-synapse")


def plugin_root() -> Path:
    """The plugin install root (replaced on update)."""
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return Path(env)
    # hooks/<thisfile> -> plugin root is one level up from hooks/
    return Path(__file__).resolve().parents[1]


def skill_root() -> Path:
    return plugin_root().joinpath(*SKILL_SUBPATH)


def scripts_dir() -> Path:
    return skill_root() / "scripts"


def summon_path() -> Path:
    return scripts_dir() / "summon.py"


def data_root() -> Path:
    """Writable data root (survives updates): user agents, memory, marker.

    1. $CLAUDE_PLUGIN_DATA (present in hook context).
    2. Derived via the scripts' own _pluginpaths resolver (single source of truth).
    3. In-place fallback: the skill root itself (portable-skill / dev checkout).
    """
    env = os.environ.get("CLAUDE_PLUGIN_DATA")
    if env:
        return Path(env)
    sk = skill_root()
    try:
        sd = str(scripts_dir())
        if sd not in sys.path:
            sys.path.insert(0, sd)
        import _pluginpaths  # type: ignore
        return Path(_pluginpaths.resolve_data_root(str(sk)))
    except Exception:
        return sk


def summon_state_dir() -> Path:
    return data_root() / ".summon-state"
