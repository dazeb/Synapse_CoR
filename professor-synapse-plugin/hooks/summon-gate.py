#!/usr/bin/env python3
"""PreToolUse hook: gate task-action tools behind an agent summon.

Professor Synapse routes every task to an owning agent and SUMMONS it
(scripts/summon.py) before doing task work. This hook enforces that: it BLOCKS
task-action tools (file edits and direct memory.py calls) until a summon has
happened THIS session.

Two levels of gating:
  * General: any summon this session unlocks file edits and memory.py READS
    (recall/brief/scan/...). summon.py itself already does recall.
  * Memory writes: memory.py WRITE subcommands (record/add/update/compact/
    forget/...) additionally require the MEMORY-AGENT to have been summoned this
    session -- all durable memory routes through the memory-agent. Summoning any
    other agent is not enough for a write.

A summon is recorded two ways, either of which lifts the gate:
  1. summon.py writes <data_root>/.summon-state/summon-<session>.json (marker).
     The marker accumulates the slugs of every agent summoned this session, so
     the gate can tell whether the memory-agent specifically was among them.
  2. (fallback) the session transcript shows a prior summon.py Bash call.

Always allowed (orientation / routing): Read, Glob, Grep, and any Bash that is
NOT a direct memory.py call -- so Professor can read SKILL/INDEX and run
summon.py itself.

Escape hatch -- if no agent owns the task, record the explicit decision instead
of silently skipping:
  python3 "<plugin>/scripts/summon.py" --self --reason "why none fits"

Fail-open: any error or missing data exits 0 (allow), so a hook bug can never
brick the session.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys
from pathlib import Path

try:
    import _hookpaths
except Exception:
    _hookpaths = None

# File-editing tools are always gated. Names differ by tool: Claude Code emits
# Edit/Write/NotebookEdit/MultiEdit; some runtimes emit apply_patch.
GATED_EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit", "apply_patch"}
# Bash is gated only when it is a direct memory.py call (memory ops must go
# through a summoned agent). summon.py itself is explicitly exempt below.
GATED_BASH_RE = re.compile(r"\bmemory\.py\b")

MEMORY_AGENT_SLUG = "memory-agent"
MEMORY_WRITE_CMDS = {
    "record", "add", "update", "resolve", "compact", "resurface",
    "forget", "link", "unlink", "reinforce", "reconfirm", "profile", "validate",
}
MEMORY_READ_CMDS = {
    "recall", "brief", "read", "scan", "agents", "links",
    "doctor", "render", "export", "check",
}

# How long a session-less ("nosession") marker stays valid, in hours.
NOSESSION_TTL_HOURS = float(os.environ.get("SUMMON_GATE_NOSESSION_TTL_HOURS", "8") or 8)


def summon_state_dir() -> Path:
    if _hookpaths is not None:
        try:
            return _hookpaths.summon_state_dir()
        except Exception:
            pass
    # Last-ditch fallback: env data dir, else beside this hook's plugin.
    env = os.environ.get("CLAUDE_PLUGIN_DATA")
    base = Path(env) if env else Path(__file__).resolve().parents[1] / "skills" / "professor-synapse"
    return base / ".summon-state"


def summon_cmd() -> str:
    if _hookpaths is not None:
        try:
            return str(_hookpaths.summon_path())
        except Exception:
            pass
    return "scripts/summon.py"


def memory_subcommand(cmd):
    """Best-effort: the memory.py subcommand in a shell command, or None."""
    tail = re.split(r"\bmemory\.py\b", cmd)[-1]
    known = MEMORY_WRITE_CMDS | MEMORY_READ_CMDS
    for tok in tail.split():
        if tok in known:
            return tok
    return None


def classify_gate(tool_name, tool_input):
    """Return (gated, is_memory_write)."""
    if tool_name in GATED_EDIT_TOOLS:
        return (True, False)
    if tool_name == "Bash":
        cmd = (tool_input or {}).get("command", "")
        if isinstance(cmd, str) and GATED_BASH_RE.search(cmd):
            if "summon.py" in cmd:   # running the summon itself is always fine
                return (False, False)
            return (True, memory_subcommand(cmd) in MEMORY_WRITE_CMDS)
    return (False, False)


def _marker_fresh(path, ttl_hours):
    try:
        ts = json.loads(path.read_text(encoding="utf-8")).get("ts")
        if not ts:
            return False
        when = datetime.datetime.fromisoformat(ts)
        now = datetime.datetime.now(when.tzinfo) if when.tzinfo else datetime.datetime.now()
        age = (now - when).total_seconds()
        return 0 <= age <= ttl_hours * 3600
    except Exception:
        return False


def _load_marker(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def resolve_marker(session_id):
    """Return the payload of the valid summon marker for this session, or None."""
    state = summon_state_dir()
    if session_id:
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", session_id)
        exact = state / f"summon-{safe}.json"
        if exact.exists():
            return _load_marker(exact) or {}
        nos = state / "summon-nosession.json"
        if nos.exists() and _marker_fresh(nos, NOSESSION_TTL_HOURS):
            return _load_marker(nos) or {}
        return None
    try:
        best, best_ts = None, ""
        for p in state.glob("summon-*.json"):
            m = _load_marker(p)
            if m is not None and str(m.get("ts", "")) >= best_ts:
                best, best_ts = m, str(m.get("ts", ""))
        return best
    except Exception:
        return None


def transcript_shows_summon(transcript_path, needle=None):
    """True if the transcript contains a Bash tool_use running summon.py."""
    if not transcript_path or not os.path.exists(transcript_path):
        return False
    try:
        with open(transcript_path, "r", encoding="utf-8") as fh:
            for line in fh:
                if "summon.py" not in line:
                    continue
                if needle and needle not in line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                msg = entry.get("message") or {}
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use" and block.get("name") == "Bash":
                        cmd = (block.get("input") or {}).get("command", "")
                        if isinstance(cmd, str) and "summon.py" in cmd:
                            if needle and needle not in cmd:
                                continue
                            return True
    except Exception:
        return False
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    if data.get("hook_event_name") not in (None, "PreToolUse"):
        return 0

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    gated, is_memory_write = classify_gate(tool_name, tool_input)
    if not gated:
        return 0

    session_id = data.get("session_id") or os.environ.get("CLAUDE_CODE_SESSION_ID")
    transcript_path = data.get("transcript_path")

    marker = resolve_marker(session_id)
    summoned = marker is not None or transcript_shows_summon(transcript_path)

    sp = summon_cmd()

    if not summoned:
        return deny(
            "SUMMON GATE: no agent has been summoned this session, so task-action "
            "tools (file edits, direct memory.py calls) are blocked.\n\n"
            "Professor Synapse requires routing the task to its owning agent and "
            "SUMMONING it BEFORE any task work -- including memory recall, reading "
            "source files for the task, planning, and editing.\n\n"
            "Do this now:\n"
            f'  python3 "{sp}" "<agent>"\n'
            "then become that agent (prefix replies with its emoji) and retry.\n\n"
            "If you genuinely confirmed no agent fits, record that decision instead "
            "of skipping it:\n"
            f'  python3 "{sp}" --self --reason "why none fits"'
        )

    if is_memory_write:
        agents = (marker or {}).get("agents") or []
        if MEMORY_AGENT_SLUG not in agents and not transcript_shows_summon(transcript_path, MEMORY_AGENT_SLUG):
            return deny(
                "MEMORY-AGENT GATE: this is a memory WRITE (memory.py write op), and "
                "all durable memory must go THROUGH the memory-agent -- which has not "
                "been summoned this session. Summoning another agent is not enough.\n\n"
                "Summon the memory-agent, then save as it:\n"
                f'  python3 "{sp}" "memory-agent"\n'
                "become it (prefix replies with the memory-agent emoji), follow "
                "references/memory-protocol.md, and retry the write.\n\n"
                "(Reads like recall/brief/scan do NOT need this -- only writes such as "
                "record/add/update/compact/forget.)"
            )

    return 0


def deny(reason):
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
