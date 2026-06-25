#!/usr/bin/env python3
"""Stop hook: nudge to save memory after N tool calls without touching memory.

Behavioral, deterministic save reminder. At each turn end it reads the session
transcript, counts assistant tool calls since the most recent memory interaction
(a Bash call running summon.py or memory.py -- a load OR a save both reset the
count), and if that count has crossed the threshold it blocks the stop with a
reminder to ASK the user whether anything durable should be saved.

Threshold: env MEMORY_NUDGE_AFTER (int), else NUDGE_AFTER below.

Debounce: a marker (<data_root>/.summon-state/nudge-<session>.json) records the
total tool-call count at the last nudge, so it re-nudges roughly every N calls
while unsaved rather than on every turn. A memory load/save naturally resets the
"since" count, pausing nudges until work accumulates again.

Fail-open: any error exits 0 (allow the stop), so a hook bug never traps a turn.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

try:
    import _hookpaths
except Exception:
    _hookpaths = None

NUDGE_AFTER = 25  # tool calls since the last memory load/save before nudging

# A tool call "touches memory" (resets the counter) when it runs either script.
MEMORY_CALL_RE = re.compile(r"\b(summon|memory)\.py\b")


def threshold():
    try:
        v = int(os.environ.get("MEMORY_NUDGE_AFTER", ""))
        return v if v > 0 else NUDGE_AFTER
    except Exception:
        return NUDGE_AFTER


def summon_state_dir() -> Path:
    if _hookpaths is not None:
        try:
            return _hookpaths.summon_state_dir()
        except Exception:
            pass
    env = os.environ.get("CLAUDE_PLUGIN_DATA")
    base = Path(env) if env else Path(__file__).resolve().parents[1] / "skills" / "professor-synapse"
    return base / ".summon-state"


def count_since_last_memory(transcript_path):
    """Return (total_tool_calls, calls_since_last_memory_interaction)."""
    total = 0
    since = 0
    if not transcript_path or not os.path.exists(transcript_path):
        return (0, 0)
    try:
        with open(transcript_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                msg = entry.get("message") or {}
                if (msg.get("role") or entry.get("role")) != "assistant":
                    continue
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    total += 1
                    inp = block.get("input") or {}
                    cmd = inp.get("command", "") if isinstance(inp, dict) else ""
                    if block.get("name") == "Bash" and isinstance(cmd, str) and MEMORY_CALL_RE.search(cmd):
                        since = 0          # a load or save resets the counter
                    else:
                        since += 1
    except Exception:
        return (0, 0)
    return (total, since)


def marker_path(session_id):
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", session_id or "nosession")
    return summon_state_dir() / f"nudge-{safe}.json"


def last_nudge_total(path):
    try:
        return int(json.loads(path.read_text(encoding="utf-8")).get("last_nudge_total", 0))
    except Exception:
        return 0


def write_nudge_total(path, total):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = str(path) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"last_nudge_total": total}, fh)
        os.replace(tmp, path)
    except Exception:
        pass


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    if data.get("hook_event_name") not in (None, "Stop"):
        return 0
    if data.get("stop_hook_active"):   # already mid-continuation; don't stack nudges
        return 0

    x = threshold()
    total, since = count_since_last_memory(data.get("transcript_path"))
    if since < x:
        return 0

    session_id = data.get("session_id") or os.environ.get("CLAUDE_CODE_SESSION_ID")
    mpath = marker_path(session_id)
    if total - last_nudge_total(mpath) < x:   # debounce: nudged within the last X calls
        return 0
    write_nudge_total(mpath, total)

    reason = (
        f"MEMORY SAVE NUDGE: ~{since} tool calls since you last loaded or saved memory, "
        "with no save in between. If anything durable has emerged this stretch -- a "
        "decision made, a reusable lesson, a user preference/correction, or project "
        "state worth keeping -- pause and ASK the user whether to save it (name what "
        "you would save and its kind: fact / decision / note / lesson), routing through "
        "the memory-agent per references/memory-protocol.md. If nothing is worth saving, "
        "say so in one line and continue. Do not silently save without asking."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
