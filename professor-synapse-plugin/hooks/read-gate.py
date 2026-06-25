#!/usr/bin/env python3
"""PreToolUse hook: require reading a category's governing doc before writing to it.

Creating an agent or a script should follow its protocol, not be improvised. This
hook enforces "read-before-write": a Write/Edit whose target lands in a gated
category dir under the writable data root (e.g. <data>/agents/, <data>/scripts/)
is BLOCKED until the session transcript shows you READ that category's governing
document. Once read, every later write to that category passes for the rest of
the session.

When it allows a gated write, it appends an audit record to
<data>/.summon-state/readdocs-<session>.json — the "track that it read the docs"
trail (category, doc, timestamp).

Extend coverage by adding entries to REQUIRED_DOCS. Disable entirely with
READ_GATE_DISABLE=1.

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

GATED_WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"}

# category dir -> governing doc(s) that must be read first (paths relative to the
# skill/data root). ALL listed docs for a category must have been read. Add
# "protocols", "templates", "references" here to gate those too.
REQUIRED_DOCS = {
    "agents": ["references/agent-template.md"],
    "scripts": ["references/scripts-protocol.md"],
}

# Recommended-but-not-required extra reading, surfaced in the nudge.
SUGGESTED_DOCS = {
    "agents": ["references/domain-expertise.md", "references/summon-agent-protocol.md"],
    "scripts": [],
}


def data_root() -> Path | None:
    if _hookpaths is not None:
        try:
            return _hookpaths.data_root()
        except Exception:
            return None
    env = os.environ.get("CLAUDE_PLUGIN_DATA")
    return Path(env) if env else None


def skill_root() -> Path | None:
    if _hookpaths is not None:
        try:
            return _hookpaths.skill_root()
        except Exception:
            return None
    return None


def resolve_doc(rel: str) -> str:
    """Absolute path to a doc, user-data copy preferred over shipped core."""
    dr, sk = data_root(), skill_root()
    if dr is not None:
        cand = dr / rel
        if cand.exists():
            return str(cand)
    if sk is not None:
        return str(sk / rel)
    return rel


def target_paths(tool_input: dict) -> list[Path]:
    """File paths a write tool touches (best-effort across tool shapes)."""
    out = []
    for key in ("file_path", "notebook_path", "path"):
        v = (tool_input or {}).get(key)
        if isinstance(v, str) and v:
            out.append(Path(v))
    return out


def category_of(path: Path) -> str | None:
    """Which gated category this path writes into, or None.

    A path is in category C when it lives under <data_root>/C or <skill_root>/C.
    """
    try:
        target = path.resolve()
    except Exception:
        target = path
    roots = [r for r in (data_root(), skill_root()) if r is not None]
    for cat in REQUIRED_DOCS:
        for root in roots:
            try:
                base = (root / cat).resolve()
            except Exception:
                continue
            try:
                if target == base or base in target.parents:
                    return cat
            except Exception:
                continue
    return None


def read_basenames(transcript_path: str) -> set:
    """Basenames of files the model READ this session (Read tool, or a Bash
    cat/head/less/sed/grep of the file). Used to tell whether a doc was read."""
    seen = set()
    if not transcript_path or not os.path.exists(transcript_path):
        return seen
    bash_read = re.compile(r"\b(cat|less|head|tail|sed|grep|view|bat)\b")
    try:
        with open(transcript_path, "r", encoding="utf-8") as fh:
            for line in fh:
                if '"tool_use"' not in line:
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
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    name = block.get("name")
                    inp = block.get("input") or {}
                    if name in ("Read", "View", "NotebookRead"):
                        fp = inp.get("file_path") or inp.get("notebook_path") or ""
                        if isinstance(fp, str) and fp:
                            seen.add(os.path.basename(fp))
                    elif name == "Bash":
                        cmd = inp.get("command", "")
                        if isinstance(cmd, str) and bash_read.search(cmd):
                            for tok in re.findall(r"[\w./-]+\.\w+", cmd):
                                seen.add(os.path.basename(tok))
    except Exception:
        return seen
    return seen


def record_audit(session_id: str, satisfied: list):
    """Append the read-doc audit trail. Best-effort; never blocks on failure."""
    dr = data_root()
    if dr is None:
        return
    try:
        state = dr / ".summon-state"
        state.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", session_id or "nosession")
        path = state / f"readdocs-{safe}.json"
        now = datetime.datetime.now().isoformat(timespec="seconds")
        existing = {"session": session_id, "satisfied": []}
        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    existing = loaded
                    existing.setdefault("satisfied", [])
            except Exception:
                pass
        have = {(r.get("category"), r.get("doc")) for r in existing["satisfied"]}
        for cat, doc in satisfied:
            if (cat, doc) not in have:
                existing["satisfied"].append({"category": cat, "doc": doc, "ts": now})
        existing["ts"] = now
        tmp = str(path) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(existing, fh, indent=2)
        os.replace(tmp, path)
    except Exception:
        pass


def main():
    if os.environ.get("READ_GATE_DISABLE"):
        return 0
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    if data.get("hook_event_name") not in (None, "PreToolUse"):
        return 0

    tool_name = data.get("tool_name", "")
    if tool_name not in GATED_WRITE_TOOLS:
        return 0

    tool_input = data.get("tool_input") or {}
    cats = set()
    for p in target_paths(tool_input):
        c = category_of(p)
        if c:
            cats.add(c)
    if not cats:
        return 0

    read = read_basenames(data.get("transcript_path"))

    missing = []   # (category, doc-rel) still unread
    satisfied = []  # (category, doc-rel) already read -> audit
    for cat in sorted(cats):
        for doc in REQUIRED_DOCS[cat]:
            if os.path.basename(doc) in read:
                satisfied.append((cat, doc))
            else:
                missing.append((cat, doc))

    if missing:
        lines = [
            "READ-BEFORE-WRITE GATE: you're creating/editing a file in a governed "
            f"folder ({', '.join(sorted(cats))}/) without having read its protocol "
            "this session. Read the document(s) below first, then retry the write:",
            "",
        ]
        for cat, doc in missing:
            lines.append(f"  [{cat}] read: {resolve_doc(doc)}")
        sugg = []
        for cat in sorted(cats):
            for doc in SUGGESTED_DOCS.get(cat, []):
                if os.path.basename(doc) not in read:
                    sugg.append(resolve_doc(doc))
        if sugg:
            lines.append("")
            lines.append("Recommended too (not required): " + "; ".join(sugg))
        lines.append("")
        lines.append("Open them with the Read tool, follow the protocol, then write. "
                     "Once read, further writes to this folder are unblocked for the session.")
        return deny("\n".join(lines))

    if satisfied:
        record_audit(data.get("session_id") or os.environ.get("CLAUDE_CODE_SESSION_ID", ""), satisfied)
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
