#!/usr/bin/env python3
"""
memory.py - Professor Synapse's shared, agent-tagged memory.

Two stores under ./memory/, one tool:
  - memory/memory.json   working memory (profile + active items). Human-readable. Hot.
  - memory/longterm.db   SQLite long-term store (records + change log). Queryable. Cold.

Every item, record, and log entry is tagged with the agent that created it, so
memory can be filtered by agent. Standard library only; no pip installs.

Top-level options:
  --agent <slug>   the active agent. Writes stamp it; reads filter by it; omit
                   on a read to see across all agents.

Verbs (run `python3 memory.py <verb> --help` for options):
  read       Show working memory (optionally one agent's).
  profile    Set shared profile fields (person-level, not agent-scoped).
  add        Add an active item, tagged with --agent.
  update     Change fields on an active item.
  resolve    Mark an active item done.
  scan       Flag stale / overdue / done / duplicate active items.
  compact    Move approved items to long-term, cap the log.
  resurface  Move an archived item back to active (same id).
  record     Write straight to long-term: a decision, note, or fact.
  recall     Find long-term items worth surfacing (by date, --query, --agent).
             --query is ranked full-text search (FTS5, with a LIKE fallback).
  brief      One-shot prefetch: profile + active items + due long-term items,
             plus --query matches. The start-of-session recall in one call.
  agents     List every agent that has touched memory, with counts.
  validate   Check memory.json; --fix applies safe mechanical repairs.
  doctor     Check long-term db integrity.
  render     Print working memory as markdown.
  export     Dump long-term db to JSON (optionally one agent's).

Persistence: this store lives inside the Professor Synapse skill. To make a change
survive, rebuild the skill per references/rebuild-protocol.md and reinstall it.
"""

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
MEM_DIR = SKILL_ROOT / "memory"
ITEM_STATUS = {"open", "done"}
RECORD_KINDS = {"item", "decision", "note", "fact", "lesson"}
RECORD_STATUS = {"open", "done", "deferred", "dropped"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
# Optional fusion nudge by confidence (applied multiplicatively when present).
CONFIDENCE_WEIGHT = {"high": 1.15, "medium": 1.0, "low": 0.85}
STALE_DAYS = 21
LOG_CAP_DAYS = 90
SCHEMA_VERSION = 1
DEFAULT_AGENT = "unknown"

# Ranked-fusion tuning for keyword recall (recall --query / brief --query).
RRF_K = 60                       # Reciprocal Rank Fusion damping; larger = flatter
W_TEXT = 1.0                     # weight of the BM25 relevance ranking
W_RECENCY = 0.5                  # weight of the recency ranking (secondary signal)
# BM25 per-column weights, in FTS index column order
# (id, text, people, tags, owner, goal, outcome, constraints).
# people/tags/constraints outrank free text: an exact tag/person/gotcha hit is a
# stronger signal. goal/outcome are weighted above plain text but below the lists.
BM25_WEIGHTS = (0.0, 1.0, 3.0, 3.0, 1.0, 2.0, 1.5, 3.0)
KIND_WEIGHT = {"fact": 1.3, "lesson": 1.25, "decision": 1.2, "note": 1.0, "item": 1.0}


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def utc_today():
    return datetime.now(timezone.utc).date().isoformat()


def working_path(root):
    return Path(root) / "memory" / "memory.json"


def db_path(root):
    return Path(root) / "memory" / "longterm.db"


def new_id():
    return f"m-{uuid.uuid4().hex[:8]}"


def _is_iso(v):
    try:
        datetime.fromisoformat(str(v))
        return True
    except ValueError:
        return False


def _ensure_dir(root):
    (Path(root) / "memory").mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# Working memory
# --------------------------------------------------------------------------

def empty_working():
    return {
        "meta": {"schema_version": SCHEMA_VERSION, "updated_at": None},
        "profile": {
            "name": None, "title": None, "notes": None,
            "focus_areas": [], "key_people": [],
        },
        "active": [],
    }


MIGRATIONS = {}  # {from_version: fn(data)->None}. See references/memory-data-model.md.


def migrate_working(data):
    meta = data.setdefault("meta", {})
    v = meta.get("schema_version", SCHEMA_VERSION)
    if v > SCHEMA_VERSION:
        sys.exit(f"memory.json is schema_version {v}, newer than this skill "
                 f"({SCHEMA_VERSION}). Reinstall the matching skill version.")
    changed = False
    while v < SCHEMA_VERSION:
        fn = MIGRATIONS.get(v)
        if fn is None:
            sys.exit(f"No migration registered from schema_version {v} to {v + 1}.")
        fn(data)
        v += 1
        meta["schema_version"] = v
        changed = True
    return changed


def load_working(root):
    p = working_path(root)
    if not p.exists():
        data = empty_working()
        save_working(root, data)
        return data
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(f"memory.json is not valid JSON: {e}. "
                 "Restore memory.json.bak or fix the file, then retry.")
    if migrate_working(data):
        save_working(root, data)
    fatal = [m for s, m in validate_working(data) if s == "fatal"]
    if fatal:
        sys.exit("memory.json has a structural problem: " + "; ".join(fatal)
                 + ". Run `validate` for details; restore memory.json.bak to recover.")
    return data


def save_working(root, data):
    fatal = [m for s, m in validate_working(data) if s == "fatal"]
    if fatal:
        raise ValueError("Refusing to write invalid memory.json: " + "; ".join(fatal))
    _ensure_dir(root)
    data.setdefault("meta", {})["updated_at"] = utc_now()
    p = working_path(root)
    if p.exists():
        shutil.copy2(p, str(p) + ".bak")
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def validate_working(data):
    out = []
    if not isinstance(data, dict):
        return [("fatal", "top level is not an object")]
    for key in ("meta", "profile", "active"):
        if key not in data:
            out.append(("fixable", f"missing top-level key '{key}'"))
    active = data.get("active", [])
    if not isinstance(active, list):
        return out + [("fatal", "'active' is not a list")]
    seen = set()
    for i, item in enumerate(active):
        if not isinstance(item, dict):
            out.append(("fatal", f"active[{i}] is not an object"))
            continue
        iid = item.get("id")
        if not iid:
            out.append(("fixable", f"active[{i}] missing id"))
        elif iid in seen:
            out.append(("fixable", f"duplicate id '{iid}'"))
        else:
            seen.add(iid)
        if not item.get("agent"):
            out.append(("fixable", f"active[{i}] missing agent"))
        if item.get("status") not in ITEM_STATUS:
            out.append(("fixable", f"active[{i}] invalid status '{item.get('status')}'"))
        for key in ("people", "tags", "constraints"):
            if key in item and not isinstance(item[key], list):
                out.append(("fixable", f"active[{i}] field '{key}' is not a list"))
        conf = item.get("confidence")
        if conf is not None and conf not in CONFIDENCE_LEVELS:
            out.append(("fixable", f"active[{i}] invalid confidence '{conf}'"))
        for d in ("due", "created_at", "updated_at"):
            v = item.get(d)
            if v and not _is_iso(v):
                out.append(("fixable", f"active[{i}] '{d}' not ISO: {v}"))
    return out


def fix_working(data):
    changes = []
    base = empty_working()
    for key in ("meta", "profile"):
        if not isinstance(data.get(key), dict):
            data[key] = base[key]
            changes.append(f"added missing {key}")
    if not isinstance(data.get("active"), list):
        data["active"] = []
        changes.append("reset active list")
    seen, cleaned = set(), []
    for item in data["active"]:
        if not isinstance(item, dict):
            changes.append("dropped a non-object active entry")
            continue
        if not item.get("id"):
            item["id"] = new_id()
            changes.append(f"assigned id {item['id']}")
        if item["id"] in seen:
            changes.append(f"dropped duplicate id {item['id']}")
            continue
        seen.add(item["id"])
        if not item.get("agent"):
            item["agent"] = DEFAULT_AGENT
            changes.append(f"set agent on {item['id']}")
        for key in ("people", "tags"):
            if not isinstance(item.get(key), list):
                item[key] = []
                changes.append(f"reset {key} on {item['id']}")
        if "constraints" in item and not isinstance(item["constraints"], list):
            item["constraints"] = []
            changes.append(f"reset constraints on {item['id']}")
        if item.get("confidence") is not None and item["confidence"] not in CONFIDENCE_LEVELS:
            item["confidence"] = None
            changes.append(f"cleared invalid confidence on {item['id']}")
        if not item.get("created_at"):
            item["created_at"] = utc_today()
            changes.append(f"backfilled created_at on {item['id']}")
        if not item.get("updated_at"):
            item["updated_at"] = item["created_at"]
            changes.append(f"backfilled updated_at on {item['id']}")
        if item.get("status") not in ITEM_STATUS:
            item["status"] = "open"
            changes.append(f"reset status on {item['id']}")
        cleaned.append(item)
    data["active"] = cleaned
    return changes


# --------------------------------------------------------------------------
# Long-term store
# --------------------------------------------------------------------------

# `kind` is validated in Python (RECORD_KINDS), not by a DB CHECK, so new kinds can
# be added without rebuilding the table. The body fields goal/outcome/constraints are
# optional and conventionally filled by `lesson` records (constraints is a JSON array).
RECORD_DDL = """
CREATE TABLE IF NOT EXISTS record (
    id          TEXT PRIMARY KEY,
    agent       TEXT,
    kind        TEXT NOT NULL,
    type        TEXT,
    text        TEXT NOT NULL,
    people      TEXT,
    tags        TEXT,
    owner       TEXT,
    due         TEXT,
    status      TEXT CHECK(status IN ('open','done','deferred','dropped')),
    source      TEXT,
    created_at  TEXT,
    recorded_at TEXT,
    reason      TEXT,
    rationale   TEXT,
    goal        TEXT,
    outcome     TEXT,
    constraints TEXT,
    confidence  TEXT
);
"""
CHANGELOG_DDL = """
CREATE TABLE IF NOT EXISTS changelog (
    seq     INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT,
    agent   TEXT,
    action  TEXT,
    item_id TEXT,
    summary TEXT
);
"""
# Columns in RECORD_DDL order — single source of truth for full-row copies.
RECORD_COLUMNS = ("id", "agent", "kind", "type", "text", "people", "tags", "owner",
                  "due", "status", "source", "created_at", "recorded_at", "reason",
                  "rationale", "goal", "outcome", "constraints", "confidence")


def _migrate_record_schema(con):
    """Bring an existing `record` table up to the current schema. Additive columns
    are added in place; the old restrictive `kind` CHECK (which forbids 'lesson') is
    removed by rebuilding the table, preserving every row. No-op on a fresh db."""
    row = con.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='record'").fetchone()
    if not row:
        return
    cols = {r[1] for r in con.execute("PRAGMA table_info(record)")}
    for c in ("goal", "outcome", "constraints", "confidence"):
        if c not in cols:
            con.execute(f"ALTER TABLE record ADD COLUMN {c} TEXT")
    if "kind IN ('item','decision','note','fact')" in (row[0] or ""):
        collist = ",".join(RECORD_COLUMNS)
        con.executescript(
            "ALTER TABLE record RENAME TO _record_old;"
            + RECORD_DDL
            + f"INSERT INTO record ({collist}) SELECT {collist} FROM _record_old;"
            + "DROP TABLE _record_old;"
        )


def connect_db(root):
    _ensure_dir(root)
    con = sqlite3.connect(str(db_path(root)))
    con.executescript(RECORD_DDL + CHANGELOG_DDL)
    _migrate_record_schema(con)
    con.commit()
    return con


def log_event(con, agent, action, item_id, summary):
    con.execute("INSERT INTO changelog(ts,agent,action,item_id,summary) VALUES(?,?,?,?,?)",
                (utc_now(), agent, action, item_id, summary))


def cap_log(con):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=LOG_CAP_DAYS)).isoformat(timespec="seconds")
    return con.execute("DELETE FROM changelog WHERE ts < ?", (cutoff,)).rowcount


def _json_list(s):
    try:
        v = json.loads(s) if s else []
        return v if isinstance(v, list) else []
    except (ValueError, TypeError):
        return []


def _check_confidence(val):
    """Normalize an optional confidence to high/medium/low, or exit with guidance."""
    if val is None:
        return None
    v = val.strip().lower()
    aliases = {"hi": "high", "h": "high", "med": "medium", "m": "medium",
               "lo": "low", "l": "low"}
    v = aliases.get(v, v)
    if v not in CONFIDENCE_LEVELS:
        sys.exit(f"--confidence must be one of {sorted(CONFIDENCE_LEVELS)} (got '{val}')")
    return v


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def cmd_read(root, args):
    data = load_working(root)
    if args.agent:
        data = dict(data)
        data["active"] = [i for i in data["active"] if i.get("agent") == args.agent]
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_profile(root, args):
    data = load_working(root)
    prof = data["profile"]
    for field in ("name", "title", "notes"):
        val = getattr(args, field)
        if val is not None:
            prof[field] = val
    if args.focus_areas is not None:
        prof["focus_areas"] = args.focus_areas
    if args.key_people is not None:
        try:
            people = json.loads(args.key_people)
            assert isinstance(people, list)
        except (ValueError, AssertionError):
            sys.exit("--key-people must be a JSON array of {name, role, note}")
        prof["key_people"] = people
    save_working(root, data)
    print("profile updated")


def cmd_add(root, args):
    data = load_working(root)
    item = {
        "id": new_id(),
        "agent": args.agent or DEFAULT_AGENT,
        "type": args.type,
        "text": args.text,
        "people": args.people or [],
        "tags": args.tags or [],
        "owner": args.owner,
        "due": args.due,
        "status": "open",
        "source": args.source,
        "goal": args.goal,
        "outcome": args.outcome,
        "constraints": args.constraints or [],
        "confidence": _check_confidence(args.confidence),
        "created_at": utc_today(),
        "updated_at": utc_today(),
    }
    data["active"].append(item)
    save_working(root, data)
    print(f"added {item['id']} [{item['agent']}]: {item['text']}")


def cmd_update(root, args):
    data = load_working(root)
    item = _find(data, args.id)
    for field in ("text", "owner", "due", "source", "status", "type", "agent",
                  "goal", "outcome"):
        val = getattr(args, field)
        if val is not None:
            item[field] = val
    if args.people is not None:
        item["people"] = args.people
    if args.tags is not None:
        item["tags"] = args.tags
    if args.constraints is not None:
        item["constraints"] = args.constraints
    if args.confidence is not None:
        item["confidence"] = _check_confidence(args.confidence)
    item["updated_at"] = utc_today()
    save_working(root, data)
    print(f"updated {item['id']}")


def cmd_resolve(root, args):
    data = load_working(root)
    item = _find(data, args.id)
    item["status"] = "done"
    item["updated_at"] = utc_today()
    save_working(root, data)
    print(f"resolved {item['id']} (run compact to archive it)")


def _find(data, item_id):
    for item in data["active"]:
        if item["id"] == item_id:
            return item
    sys.exit(f"no active item with id '{item_id}'")


def cmd_scan(root, args):
    data = load_working(root)
    today = datetime.now(timezone.utc).date()
    items = data["active"]
    if args.agent:
        items = [i for i in items if i.get("agent") == args.agent]
    overdue, done, stale, dupes = [], [], [], []
    by_text = {}
    for item in items:
        if item.get("status") == "done":
            done.append(item["id"])
        due = item.get("due")
        if item.get("status") == "open" and due and _is_iso(due):
            if datetime.fromisoformat(due).date() < today:
                overdue.append(item["id"])
        upd = item.get("updated_at")
        if item.get("status") == "open" and upd and _is_iso(upd):
            if datetime.fromisoformat(upd).date() < today - timedelta(days=STALE_DAYS):
                stale.append(item["id"])
        key = re.sub(r"\s+", " ", (item.get("text") or "").strip().lower())
        by_text.setdefault(key, []).append(item["id"])
    for ids in by_text.values():
        if len(ids) > 1:
            dupes.append(ids)
    print(json.dumps({"overdue": overdue, "done": done, "stale_days": STALE_DAYS,
                      "stale": stale, "duplicates": dupes, "count": len(items)}, indent=2))


def cmd_compact(root, args):
    data = load_working(root)
    con = connect_db(root)
    moved = []
    for iid in (args.archive or []):
        moved.append(_to_record(data, con, iid, status=None, reason=args.reason))
    for iid in (args.drop or []):
        moved.append(_to_record(data, con, iid, status="dropped",
                                 reason=args.reason or "dropped during compaction"))
    data["active"] = [i for i in data["active"] if i["id"] not in moved]
    pruned = cap_log(con)
    con.commit()
    con.close()
    save_working(root, data)
    print(f"moved {len(moved)} item(s) to long-term; pruned {pruned} old log row(s)")


def _to_record(data, con, item_id, status, reason):
    item = next((i for i in data["active"] if i["id"] == item_id), None)
    if item is None:
        sys.exit(f"no active item with id '{item_id}' to archive")
    final_status = status or ("done" if item.get("status") == "done" else "open")
    con.execute(
        "INSERT OR REPLACE INTO record"
        "(id,agent,kind,type,text,people,tags,owner,due,status,source,created_at,"
        "recorded_at,reason,rationale,goal,outcome,constraints,confidence)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (item["id"], item.get("agent"), "item", item.get("type"), item.get("text"),
         json.dumps(item.get("people") or []), json.dumps(item.get("tags") or []),
         item.get("owner"), item.get("due"), final_status, item.get("source"),
         item.get("created_at"), utc_now(), reason, None,
         item.get("goal"), item.get("outcome"),
         json.dumps(item.get("constraints") or []), item.get("confidence")),
    )
    log_event(con, item.get("agent"), "drop" if status == "dropped" else "archive",
              item["id"], f"{item.get('type')}: {item.get('text')}")
    return item["id"]


def cmd_resurface(root, args):
    data = load_working(root)
    con = connect_db(root)
    row = con.execute(
        "SELECT id,agent,type,text,people,tags,owner,due,source,created_at,"
        "goal,outcome,constraints,confidence FROM record "
        "WHERE id=? AND kind='item'", (args.id,)).fetchone()
    if row is None:
        con.close()
        sys.exit(f"no archived item with id '{args.id}'")
    item = {
        "id": row[0], "agent": row[1], "type": row[2], "text": row[3],
        "people": _json_list(row[4]), "tags": _json_list(row[5]),
        "owner": row[6], "due": row[7], "status": "open", "source": row[8],
        "goal": row[10], "outcome": row[11],
        "constraints": _json_list(row[12]), "confidence": row[13],
        "created_at": row[9] or utc_today(), "updated_at": utc_today(),
    }
    con.execute("DELETE FROM record WHERE id=?", (args.id,))
    log_event(con, item["agent"], "resurface", args.id, item["text"])
    con.commit()
    con.close()
    data["active"].append(item)
    save_working(root, data)
    print(f"resurfaced {item['id']} [{item['agent']}]: {item['text']}")


def cmd_record(root, args):
    if args.kind not in RECORD_KINDS:
        sys.exit(f"--kind must be one of {sorted(RECORD_KINDS)}")
    con = connect_db(root)
    rid = new_id()
    con.execute(
        "INSERT INTO record"
        "(id,agent,kind,type,text,people,tags,owner,due,status,source,created_at,"
        "recorded_at,reason,rationale,goal,outcome,constraints,confidence)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (rid, args.agent or DEFAULT_AGENT, args.kind, args.type, args.text,
         json.dumps(args.people or []), json.dumps(args.tags or []),
         None, None, "done", args.source, utc_today(), utc_now(), None, args.rationale,
         args.goal, args.outcome, json.dumps(args.constraints or []),
         _check_confidence(args.confidence)),
    )
    log_event(con, args.agent or DEFAULT_AGENT, args.kind, rid, args.text)
    con.commit()
    con.close()
    print(f"recorded {args.kind} {rid} [{args.agent or DEFAULT_AGENT}]: {args.text}")


RECALL_COLS = ("id,agent,kind,type,text,people,tags,due,status,"
               "goal,outcome,constraints,confidence")


def _row_to_hit(r, why):
    hit = {"id": r[0], "agent": r[1], "kind": r[2], "type": r[3], "text": r[4],
           "people": _json_list(r[5]), "tags": _json_list(r[6]),
           "due": r[7], "status": r[8], "why": why}
    goal, outcome, constraints, confidence = r[9], r[10], r[11], r[12]
    if goal:
        hit["goal"] = goal
    if outcome:
        hit["outcome"] = outcome
    constraints = _json_list(constraints)
    if constraints:
        hit["constraints"] = constraints
    if confidence:
        hit["confidence"] = confidence
    return hit


def _due_hits(con, agent):
    """Open long-term items whose due date has arrived."""
    clause = " AND agent = ?" if agent else ""
    a = (agent,) if agent else ()
    rows = con.execute(
        f"SELECT {RECALL_COLS} FROM record WHERE kind='item' AND status NOT IN ('done','dropped') "
        f"AND due IS NOT NULL AND due <= ?{clause} ORDER BY due",
        (utc_today(), *a)).fetchall()
    return [_row_to_hit(r, "due date reached") for r in rows]


def _fts_expr(terms):
    """Build a forgiving FTS5 MATCH expression: each word becomes a prefix token,
    OR-ed together. Stripping to \\w tokens drops FTS operators so user input can
    never produce a syntax error."""
    toks = []
    for term in terms or []:
        for w in re.findall(r"\w+", term.lower()):
            toks.append(w + "*")
    return " OR ".join(dict.fromkeys(toks))  # dedupe, keep order


def _fts_ranked(con, terms, agent, pool):
    """Retrieve candidates for `terms` from a transient FTS5 index, scored by
    column-weighted BM25 (smaller = better). Returns up to `pool` (id, score) rows
    best-first, or None if FTS5 is unavailable."""
    expr = _fts_expr(terms)
    if not expr:
        return []
    try:
        con.execute("DROP TABLE IF EXISTS recall_fts")
        con.execute("CREATE VIRTUAL TABLE temp.recall_fts USING fts5("
                    "id UNINDEXED, text, people, tags, owner, goal, outcome, constraints, "
                    "tokenize='porter unicode61')")
    except sqlite3.OperationalError:
        return None  # FTS5 not compiled in
    clause = " WHERE agent = ?" if agent else ""
    a = (agent,) if agent else ()
    rows = con.execute(
        f"SELECT id,text,people,tags,owner,goal,outcome,constraints FROM record{clause}",
        a).fetchall()
    con.executemany(
        "INSERT INTO recall_fts(id,text,people,tags,owner,goal,outcome,constraints) "
        "VALUES(?,?,?,?,?,?,?,?)",
        [(r[0], r[1] or "", " ".join(_json_list(r[2])), " ".join(_json_list(r[3])),
          r[4] or "", r[5] or "", r[6] or "", " ".join(_json_list(r[7])))
         for r in rows])
    weights = ", ".join(str(w) for w in BM25_WEIGHTS)
    try:
        matched = con.execute(
            f"SELECT id, bm25(recall_fts, {weights}) AS s FROM recall_fts "
            "WHERE recall_fts MATCH ? ORDER BY s LIMIT ?",
            (expr, pool)).fetchall()
    finally:
        con.execute("DROP TABLE IF EXISTS recall_fts")
    return [(m[0], m[1]) for m in matched]


def _competition_rank(items, key, reverse=False):
    """Map each item to a 0-based rank; equal keys share a rank (so a secondary
    signal can break genuine ties rather than arbitrary retrieval order)."""
    pos, prev, rank = {}, object(), 0
    for idx, it in enumerate(sorted(items, key=key, reverse=reverse)):
        k = key(it)
        if k != prev:
            rank, prev = idx, k
        pos[it] = rank
    return pos


def _like_hits(con, terms, agent, limit):
    """Substring fallback used only when FTS5 is unavailable."""
    clause = " AND agent = ?" if agent else ""
    a = (agent,) if agent else ()
    out, seen = [], set()
    for term in terms:
        like = f"%{term}%"
        for r in con.execute(
            f"SELECT {RECALL_COLS} FROM record "
            f"WHERE (text LIKE ? OR people LIKE ? OR tags LIKE ? OR owner LIKE ?){clause} "
            "ORDER BY recorded_at DESC LIMIT ?",
            (like, like, like, like, *a, limit)).fetchall():
            if r[0] not in seen:
                seen.add(r[0])
                out.append(_row_to_hit(r, f"matches '{term}'"))
    return out


def _query_hits(con, terms, agent, limit=10):
    """Ranked keyword search over long-term records. Retrieves with FTS5, then
    re-ranks by fusing relevance + recency + kind (see fusion constants). Falls back
    to substring LIKE if FTS5 is unavailable."""
    if not terms:
        return []
    ranked = _fts_ranked(con, terms, agent, max(limit * 3, 30))
    if ranked is None:
        return _like_hits(con, terms, agent, limit)
    if not ranked:
        return []
    bm25 = dict(ranked)
    ids = list(bm25)
    placeholders = ",".join("?" for _ in ids)
    rows = con.execute(
        f"SELECT {RECALL_COLS},recorded_at FROM record WHERE id IN ({placeholders})", ids).fetchall()
    by_id = {r[0]: r for r in rows}
    # dropped records were retired on purpose — keep them out of query results
    cand = [i for i in ids if i in by_id and by_id[i][8] != "dropped"]
    # Two ranked lists fused with RRF: relevance (BM25, smaller=better) and recency.
    # Equal BM25 scores share a rank, so recency genuinely breaks ties.
    text_pos = _competition_rank(cand, key=lambda i: bm25[i])
    rec_pos = _competition_rank(cand, key=lambda i: by_id[i][13] or "", reverse=True)

    def score(i):
        rrf = W_TEXT / (RRF_K + text_pos[i]) + W_RECENCY / (RRF_K + rec_pos[i])
        kind_w = KIND_WEIGHT.get(by_id[i][2], 1.0)          # by_id[i][2] = kind
        conf_w = CONFIDENCE_WEIGHT.get(by_id[i][12], 1.0)   # by_id[i][12] = confidence
        return rrf * kind_w * conf_w

    why = "matches " + " ".join(terms)
    ranked_ids = sorted(cand, key=score, reverse=True)[:limit]
    return [_row_to_hit(by_id[i], why) for i in ranked_ids]


def _merge_hits(*groups):
    """Concatenate hit groups, keeping the first occurrence of each id."""
    out, seen = [], set()
    for group in groups:
        for h in group:
            if h["id"] not in seen:
                seen.add(h["id"])
                out.append(h)
    return out


def cmd_recall(root, args):
    con = connect_db(root)
    hits = _merge_hits(_due_hits(con, args.agent),
                       _query_hits(con, args.query or [], args.agent))
    con.close()
    print(json.dumps({"candidates": hits}, indent=2, ensure_ascii=False))


def cmd_brief(root, args):
    data = load_working(root)
    active = data["active"]
    if args.agent:
        active = [i for i in active if i.get("agent") == args.agent]
    con = connect_db(root)
    due = _due_hits(con, args.agent)
    matches = []
    if args.query:
        seen = {h["id"] for h in due}
        matches = [m for m in _query_hits(con, args.query, args.agent) if m["id"] not in seen]
    con.close()
    out = {"agent": args.agent, "profile": data["profile"], "active": active, "due": due}
    if args.query:
        out["matches"] = matches
    print(json.dumps(out, indent=2, ensure_ascii=False))


def cmd_agents(root, args):
    data = load_working(root)
    counts = {}
    for item in data["active"]:
        a = item.get("agent") or DEFAULT_AGENT
        counts.setdefault(a, {"active": 0, "longterm": 0})
        counts[a]["active"] += 1
    con = connect_db(root)
    for agent, n in con.execute("SELECT agent, COUNT(*) FROM record GROUP BY agent").fetchall():
        a = agent or DEFAULT_AGENT
        counts.setdefault(a, {"active": 0, "longterm": 0})
        counts[a]["longterm"] += n
    con.close()
    print(json.dumps(counts, indent=2, ensure_ascii=False))


def cmd_validate(root, args):
    p = working_path(root)
    if not p.exists():
        print("memory.json does not exist yet (nothing to validate).")
        return
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(json.dumps([{"severity": "fatal", "issue": f"not valid JSON: {e}"}], indent=2))
        if args.fix:
            print("\nCannot auto-fix unparseable JSON. Restore memory.json.bak.")
        return
    problems = validate_working(data)
    if not problems:
        print("memory.json is valid.")
        return
    print(json.dumps([{"severity": s, "issue": m} for s, m in problems], indent=2))
    if args.fix:
        fatal = [m for s, m in problems if s == "fatal"]
        if fatal:
            print("\nNot auto-fixing: fatal issues need human review:")
            for m in fatal:
                print(f"  - {m}")
            return
        changes = fix_working(data)
        save_working(root, data)
        print("\nApplied safe fixes (backup at memory.json.bak):")
        for c in changes:
            print(f"  - {c}")


def cmd_doctor(root, args):
    con = connect_db(root)
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    issues = []
    for r in con.execute("SELECT id,kind,status,due,created_at FROM record").fetchall():
        if r[1] not in RECORD_KINDS:
            issues.append(f"record {r[0]}: invalid kind {r[1]}")
        if r[2] and r[2] not in RECORD_STATUS:
            issues.append(f"record {r[0]}: invalid status {r[2]}")
        for label, v in (("due", r[3]), ("created_at", r[4])):
            if v and not _is_iso(v):
                issues.append(f"record {r[0]}: {label} not ISO: {v}")
    n_rec = con.execute("SELECT COUNT(*) FROM record").fetchone()[0]
    n_log = con.execute("SELECT COUNT(*) FROM changelog").fetchone()[0]
    con.close()
    print(json.dumps({"integrity_check": integrity, "invariant_issues": issues,
                      "record_rows": n_rec, "changelog_rows": n_log}, indent=2))


def cmd_render(root, args):
    data = load_working(root)
    p = data["profile"]
    people = []
    for kp in (p.get("key_people") or []):
        if isinstance(kp, dict):
            bit = kp.get("name", "")
            if kp.get("role"):
                bit += f" ({kp['role']})"
            people.append(bit)
        else:
            people.append(str(kp))
    lines = [f"# Memory for {p.get('name') or '(unnamed)'}", "",
             f"**Title:** {p.get('title') or '-'}",
             f"**Notes:** {p.get('notes') or '-'}",
             f"**Focus areas:** {', '.join(p.get('focus_areas') or []) or '-'}",
             f"**Key people:** {', '.join(people) or '-'}", "", "## Active items"]
    items = data["active"]
    if args.agent:
        items = [i for i in items if i.get("agent") == args.agent]
    if not items:
        lines.append("- (none)")
    for i in items:
        flag = " [done]" if i.get("status") == "done" else ""
        due = f" (due {i['due']})" if i.get("due") else ""
        lines.append(f"- [{i.get('agent')}] {i.get('text')}{due}{flag}  `{i['id']}`")
    print("\n".join(lines))


def cmd_export(root, args):
    con = connect_db(root)
    where = " WHERE agent = ?" if args.agent else ""
    a = (args.agent,) if args.agent else ()

    def dump(table, filt):
        cur = con.execute(f"SELECT * FROM {table}{filt}", a)
        names = [c[0] for c in cur.description]
        return [dict(zip(names, row)) for row in cur.fetchall()]
    out = {"record": dump("record", where), "changelog": dump("changelog", where)}
    con.close()
    print(json.dumps(out, indent=2, ensure_ascii=False))


# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(description="Professor Synapse shared memory CLI.")
    p.add_argument("--root", default=str(SKILL_ROOT))
    p.add_argument("--agent", help="active agent slug; writes stamp it, reads filter by it")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("read", help="show working memory (optionally one agent's)")

    pr = sub.add_parser("profile", help="set shared profile fields")
    pr.add_argument("--name")
    pr.add_argument("--title")
    pr.add_argument("--notes")
    pr.add_argument("--focus-areas", dest="focus_areas", nargs="*")
    pr.add_argument("--key-people", dest="key_people", help="JSON array of {name, role, note}")

    a = sub.add_parser("add", help="add an active item")
    a.add_argument("--type", help="free-form sub-type the agent defines")
    a.add_argument("--text", required=True)
    a.add_argument("--people", nargs="*")
    a.add_argument("--tags", nargs="*")
    a.add_argument("--owner")
    a.add_argument("--due", help="ISO date YYYY-MM-DD")
    a.add_argument("--source")
    a.add_argument("--goal", help="what this item is in service of")
    a.add_argument("--outcome", help="what resulted / current state")
    a.add_argument("--constraints", nargs="*", help="gotchas/limits (each one a quoted phrase)")
    a.add_argument("--confidence", help="high | medium | low")

    u = sub.add_parser("update", help="update fields on an active item")
    u.add_argument("--id", required=True)
    u.add_argument("--text")
    u.add_argument("--people", nargs="*")
    u.add_argument("--tags", nargs="*")
    u.add_argument("--owner")
    u.add_argument("--due")
    u.add_argument("--source")
    u.add_argument("--status", choices=sorted(ITEM_STATUS))
    u.add_argument("--type")
    u.add_argument("--agent", dest="agent")
    u.add_argument("--goal")
    u.add_argument("--outcome")
    u.add_argument("--constraints", nargs="*", help="replaces the gotcha list")
    u.add_argument("--confidence", help="high | medium | low")

    r = sub.add_parser("resolve", help="mark an active item done")
    r.add_argument("--id", required=True)

    sub.add_parser("scan", help="flag stale/overdue/done/duplicate active items")

    c = sub.add_parser("compact", help="move approved items to long-term, cap the log")
    c.add_argument("--archive", nargs="*", help="ids to archive")
    c.add_argument("--drop", nargs="*", help="ids to retire (kept in long-term)")
    c.add_argument("--reason")

    rs = sub.add_parser("resurface", help="move an archived item back to active")
    rs.add_argument("--id", required=True)

    rec = sub.add_parser("record", help="write straight to long-term")
    rec.add_argument("--kind", required=True, choices=sorted(RECORD_KINDS),
                     help="lesson = a reusable how-to (fills goal/outcome/constraints)")
    rec.add_argument("--text", required=True)
    rec.add_argument("--rationale")
    rec.add_argument("--type")
    rec.add_argument("--people", nargs="*")
    rec.add_argument("--tags", nargs="*")
    rec.add_argument("--source")
    rec.add_argument("--goal", help="what was being attempted (esp. for lessons)")
    rec.add_argument("--outcome", help="what resulted (esp. for lessons)")
    rec.add_argument("--constraints", nargs="*", help="gotchas/limits (each a quoted phrase)")
    rec.add_argument("--confidence", help="high | medium | low (esp. for facts)")

    rc = sub.add_parser("recall", help="find long-term items worth surfacing")
    rc.add_argument("--query", nargs="*", help="people or topics to search (ranked FTS5)")

    br = sub.add_parser("brief", help="one-shot prefetch: profile + active + due (+ --query)")
    br.add_argument("--query", nargs="*", help="optional people/topics to also surface from long-term")

    sub.add_parser("agents", help="list agents that have touched memory, with counts")

    v = sub.add_parser("validate", help="validate memory.json")
    v.add_argument("--fix", action="store_true")

    sub.add_parser("doctor", help="check long-term db integrity")
    sub.add_parser("render", help="print working memory as markdown")
    sub.add_parser("export", help="dump long-term db to JSON")
    return p


DISPATCH = {
    "read": cmd_read, "profile": cmd_profile, "add": cmd_add, "update": cmd_update,
    "resolve": cmd_resolve, "scan": cmd_scan, "compact": cmd_compact,
    "resurface": cmd_resurface, "record": cmd_record, "recall": cmd_recall,
    "brief": cmd_brief, "agents": cmd_agents, "validate": cmd_validate, "doctor": cmd_doctor,
    "render": cmd_render, "export": cmd_export,
}


# List-valued options use nargs="*", so they accept space-separated values
# (--tags a b). Agents and users also naturally type comma-separated values
# (--tags a,b) — normalize both forms to a clean list of distinct tokens.
# Short-token fields where comma-splitting is helpful. constraints is intentionally
# excluded: each gotcha is a phrase that may itself contain a comma.
_MULTI_FIELDS = ("people", "tags", "query", "focus_areas", "archive", "drop")


def _split_multi(values):
    out = []
    for v in values:
        for part in str(v).split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out


def normalize_multi(args):
    for field in _MULTI_FIELDS:
        val = getattr(args, field, None)
        if val is not None:
            setattr(args, field, _split_multi(val))
    return args


def main(argv=None):
    args = normalize_multi(build_parser().parse_args(argv))
    DISPATCH[args.cmd](args.root, args)


if __name__ == "__main__":
    main()
