#!/usr/bin/env python3
"""Stop hook: keep the active agent persona marker present.

Reads the Stop-hook JSON on stdin and checks the latest assistant message for
an emoji-like agent prefix. A response is "in persona" if it leads with the
Professor Synapse wizard OR any summoned agent's emoji. The summon protocol says
a summoned agent speaks with its OWN emoji and Professor steps back, so the hook
accepts agent emojis, not just the wizard. If the persona drifted (no emoji
prefix at all), the hook blocks the stop and tells the model to re-establish
character itself — a light re-read of the current agent when it just slipped, or
a full re-bootstrap through Professor Synapse when it has lost the thread. It
does NOT dump the skill inline; it points at the files to reload.

Fail-open everywhere: any error or missing data exits 0 with no output.
"""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
import sys
from typing import Any

try:
    import _hookpaths
except Exception:
    _hookpaths = None

# Broad ranges that cover common emoji prefixes used by Professor Synapse and
# summoned agents: pictographs, symbols, dingbats, flags, and related blocks.
EMOJI_RANGES = (
    (0x1F000, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2300, 0x23FF),
    (0x2B00, 0x2BFF),
)


def last_assistant_text_from_transcript(transcript_path: str) -> str:
    text = ""
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
            role = msg.get("role") or entry.get("role")
            if role != "assistant":
                continue

            content = msg.get("content")
            if isinstance(content, str):
                chunk = content
            elif isinstance(content, list):
                chunk = "".join(
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
            else:
                chunk = ""

            if chunk.strip():
                text = chunk
    return text


def read_hook_input() -> "dict[str, Any] | None":
    """Read and parse the hook JSON from stdin, UTF-8 first.

    Critical on Windows: sys.stdin uses the platform text layer (cp1252), but
    Claude Code pipes UTF-8 JSON containing the agent emoji and other multibyte
    characters. Reading raw bytes and decoding UTF-8 explicitly makes the hook
    OS-independent; WSL/Linux already defaulted to UTF-8.
    """
    try:
        raw = sys.stdin.buffer.read()
    except Exception:
        return None
    for encoding in ("utf-8", "cp1252"):
        try:
            return json.loads(raw.decode(encoding))
        except Exception:
            continue
    return None


def is_emoji_codepoint(char: str) -> bool:
    codepoint = ord(char)
    return any(start <= codepoint <= end for start, end in EMOJI_RANGES)


def starts_with_emoji(text: str) -> bool:
    stripped = html.unescape(text).lstrip("﻿​‌‍ \t\r\n")
    if not stripped:
        return False
    for char in stripped[:32]:
        if is_emoji_codepoint(char):
            return True
        if char.isalnum():
            return False
    return False


def skill_md_path() -> Path:
    if _hookpaths is not None:
        try:
            return _hookpaths.skill_root() / "SKILL.md"
        except Exception:
            pass
    return Path(__file__).resolve().parents[1] / "skills" / "professor-synapse" / "SKILL.md"


def main() -> int:
    data = read_hook_input()
    if data is None:
        return 0

    if data.get("hook_event_name") not in (None, "Stop"):
        return 0

    # Loop guard: if this hook already caused one continuation, let the turn end.
    if data.get("stop_hook_active"):
        return 0

    text = data.get("last_assistant_message")
    if not isinstance(text, str) or not text.strip():
        transcript_path = data.get("transcript_path")
        if isinstance(transcript_path, str) and transcript_path:
            try:
                text = last_assistant_text_from_transcript(transcript_path)
            except Exception:
                text = ""
        else:
            text = ""

    if not text or starts_with_emoji(text):
        return 0

    skill_path = skill_md_path()
    agents_index = skill_path.parent / "agents" / "INDEX.md"
    summon_path = skill_path.parent / "scripts" / "summon.py"

    reason = (
        "PERSONA DRIFT DETECTED: your last response did not begin with the "
        "active agent's emoji prefix. Re-establish character now and prefix "
        "this and every following message with the active agent's emoji.\n\n"
        "Choose the lightest fix that works:\n"
        "- Quick nudge: re-read the file of the agent you're currently "
        "embodying (your last summoned agent) to refresh its voice, then "
        "continue with its emoji.\n"
        "- Full re-bootstrap (only if the active agent is unclear or you've "
        f"fully drifted): re-read Professor Synapse at {skill_path}, browse the "
        f"roster with `python3 \"{summon_path}\" --list` (or the index at "
        f"{agents_index}), then re-summon the right agent via "
        f"`python3 \"{summon_path}\" \"<agent>\"` and speak with its emoji."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
