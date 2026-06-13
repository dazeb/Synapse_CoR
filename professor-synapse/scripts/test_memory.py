#!/usr/bin/env python3
"""Test suite for memory.py — Professor Synapse's shared memory CLI.

Standard library only (unittest); no pip installs, mirroring memory.py itself.
Run from anywhere:  python3 scripts/test_memory.py   (or: python3 -m unittest)
Each test runs against an isolated temp root, so the shipped store is never touched.
"""

import contextlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory  # noqa: E402


class MemTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(prefix="psmem-test-")
        self.root = self.dir.name
        os.makedirs(os.path.join(self.root, "memory"), exist_ok=True)

    def tearDown(self):
        self.dir.cleanup()

    # -- helpers ------------------------------------------------------------
    # NB: not named run()/run_json() — TestCase.run is the framework's driver.
    def cli(self, *argv):
        """Invoke the CLI with --root injected; return stdout text."""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            memory.main(["--root", self.root, *argv])
        return buf.getvalue()

    def cli_json(self, *argv):
        return json.loads(self.cli(*argv))

    def db(self):
        return sqlite3.connect(os.path.join(self.root, "memory", "longterm.db"))

    def id_by_text(self, text):
        con = self.db()
        row = con.execute("SELECT id FROM record WHERE text=?", (text,)).fetchone()
        con.close()
        return row[0] if row else None

    def set_recorded_at(self, item_id, ts):
        con = self.db()
        con.execute("UPDATE record SET recorded_at=? WHERE id=?", (ts, item_id))
        con.commit()
        con.close()

    def texts(self, candidates):
        return [c["text"] for c in candidates]


class WorkingMemory(MemTest):
    def test_add_read_roundtrip(self):
        self.cli("--agent", "alpha", "add", "--text", "ship the thing", "--tags", "work")
        data = self.cli_json("read")
        self.assertEqual(len(data["active"]), 1)
        item = data["active"][0]
        self.assertEqual(item["text"], "ship the thing")
        self.assertEqual(item["agent"], "alpha")
        self.assertEqual(item["status"], "open")
        self.assertTrue(item["id"].startswith("m-"))

    def test_read_agent_filter(self):
        self.cli("--agent", "alpha", "add", "--text", "a-task")
        self.cli("--agent", "beta", "add", "--text", "b-task")
        self.assertEqual(len(self.cli_json("read")["active"]), 2)
        only = self.cli_json("--agent", "alpha", "read")
        self.assertEqual([i["text"] for i in only["active"]], ["a-task"])

    def test_profile_roundtrip(self):
        self.cli("profile", "--name", "Jordan", "--focus-areas", "ai", "ops")
        prof = self.cli_json("read")["profile"]
        self.assertEqual(prof["name"], "Jordan")
        self.assertEqual(prof["focus_areas"], ["ai", "ops"])

    def test_resolve_marks_done(self):
        self.cli("--agent", "a", "add", "--text", "do it")
        iid = self.cli_json("read")["active"][0]["id"]
        self.cli("resolve", "--id", iid)
        self.assertEqual(self.cli_json("read")["active"][0]["status"], "done")

    def test_update_fields(self):
        self.cli("--agent", "a", "add", "--text", "draft")
        iid = self.cli_json("read")["active"][0]["id"]
        self.cli("update", "--id", iid, "--text", "final", "--tags", "x", "y")
        item = self.cli_json("read")["active"][0]
        self.assertEqual(item["text"], "final")
        self.assertEqual(item["tags"], ["x", "y"])

    def test_tags_comma_or_space_separated(self):
        # An agent may type --tags a,b OR --tags a b; both must yield distinct tags.
        self.cli("--agent", "a", "add", "--text", "comma form", "--tags", "test,install")
        self.cli("--agent", "a", "add", "--text", "space form", "--tags", "test", "install")
        self.cli("--agent", "a", "add", "--text", "mixed form",
                 "--tags", "test, install", "extra")
        active = self.cli_json("read")["active"]
        by_text = {i["text"]: i["tags"] for i in active}
        self.assertEqual(by_text["comma form"], ["test", "install"])
        self.assertEqual(by_text["space form"], ["test", "install"])
        self.assertEqual(by_text["mixed form"], ["test", "install", "extra"])


class LongTerm(MemTest):
    def test_record_then_query(self):
        self.cli("--agent", "a", "record", "--kind", "fact",
                 "--text", "Alice owns billing", "--people", "Alice", "--tags", "billing")
        hits = self.cli_json("recall", "--query", "billing")["candidates"]
        self.assertEqual(len(hits), 1)
        self.assertIn("Alice owns billing", hits[0]["text"])

    def test_compact_archive_and_resurface(self):
        self.cli("--agent", "a", "add", "--text", "archive me")
        iid = self.cli_json("read")["active"][0]["id"]
        self.cli("compact", "--archive", iid)
        self.assertEqual(self.cli_json("read")["active"], [])
        con = self.db()
        self.assertEqual(con.execute("SELECT COUNT(*) FROM record WHERE id=?", (iid,)).fetchone()[0], 1)
        con.close()
        self.cli("resurface", "--id", iid)
        back = self.cli_json("read")["active"]
        self.assertEqual(len(back), 1)
        self.assertEqual(back[0]["id"], iid)  # same id for life

    def test_recall_due_surfaces_past_due_archived_item(self):
        self.cli("--agent", "a", "add", "--text", "call vendor", "--due", "2020-01-01")
        iid = self.cli_json("read")["active"][0]["id"]
        self.cli("compact", "--archive", iid)
        hits = self.cli_json("recall")["candidates"]
        self.assertEqual([h["id"] for h in hits], [iid])
        self.assertEqual(hits[0]["why"], "due date reached")

    def test_agents_counts(self):
        self.cli("--agent", "a", "add", "--text", "x")
        self.cli("--agent", "b", "record", "--kind", "note", "--text", "y")
        counts = self.cli_json("agents")
        self.assertEqual(counts["a"]["active"], 1)
        self.assertEqual(counts["b"]["longterm"], 1)


class Search(MemTest):
    def seed(self, text, kind="note", agent="a", **kw):
        argv = ["--agent", agent, "record", "--kind", kind, "--text", text]
        for k, v in kw.items():
            argv += [f"--{k}", *( v if isinstance(v, list) else [v])]
        self.cli(*argv)
        return self.id_by_text(text)

    def test_stemming(self):
        self.seed("Acme contract renewals are quarterly")
        self.assertTrue(self.cli_json("recall", "--query", "renew")["candidates"],
                        "porter stemming should match renewals from 'renew'")

    def test_prefix(self):
        self.seed("Client onboarding checklist")
        self.assertTrue(self.cli_json("recall", "--query", "onboard")["candidates"],
                        "prefix match should match onboarding from 'onboard'")

    def test_special_chars_no_crash(self):
        self.seed("billing for Alice")
        hits = self.cli_json("recall", "--query", "alice's!! (billing)")["candidates"]
        self.assertEqual(len(hits), 1)  # operators stripped, still matches

    def test_no_match_empty(self):
        self.seed("totally unrelated")
        self.assertEqual(self.cli_json("recall", "--query", "zzzznope")["candidates"], [])

    def test_column_weighting_tag_beats_body(self):
        # both match 'acme'; one in tags, one only deep in free text. Tag hit should win.
        body = self.seed("a long note mentioning acme somewhere in the middle of prose")
        tag = self.seed("renewal terms", tags=["acme"])
        for i in (body, tag):
            self.set_recorded_at(i, "2026-01-01T00:00:00+00:00")  # equal recency
        order = [h["id"] for h in self.cli_json("recall", "--query", "acme")["candidates"]]
        self.assertEqual(order[0], tag, "tag/people columns are weighted above free text")

    def test_recency_breaks_relevance_tie(self):
        old = self.seed("acme contract alpha")  # identical relevance for 'acme'
        new = self.seed("acme contract bravo")
        self.set_recorded_at(old, "2026-01-01T00:00:00+00:00")
        self.set_recorded_at(new, "2026-06-01T00:00:00+00:00")
        order = [h["id"] for h in self.cli_json("recall", "--query", "acme")["candidates"]]
        self.assertEqual(order, [new, old], "newer record wins an equal-relevance tie")

    def test_kind_weight_breaks_tie(self):
        note = self.seed("acme thing one", kind="note")
        fact = self.seed("acme thing two", kind="fact")
        ts = "2026-03-01T00:00:00+00:00"
        self.set_recorded_at(note, ts)
        self.set_recorded_at(fact, ts)  # equal recency + equal relevance -> kind decides
        order = [h["id"] for h in self.cli_json("recall", "--query", "acme")["candidates"]]
        self.assertEqual(order[0], fact, "fact outranks note at equal relevance/recency")

    def test_dropped_excluded(self):
        self.cli("--agent", "a", "add", "--text", "obsolete acme idea")
        iid = self.cli_json("read")["active"][0]["id"]
        self.cli("compact", "--drop", iid, "--reason", "obsolete")
        self.assertEqual(self.cli_json("recall", "--query", "acme")["candidates"], [],
                         "dropped records must not resurface in query results")

    def test_like_fallback_when_fts_unavailable(self):
        self.seed("Alice handles billing", tags=["finance"])
        orig = memory._fts_ranked
        memory._fts_ranked = lambda *a, **k: None  # simulate no FTS5
        try:
            hits = self.cli_json("recall", "--query", "billing")["candidates"]
        finally:
            memory._fts_ranked = orig
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["why"], "matches 'billing'")


class Brief(MemTest):
    def test_shape_without_query(self):
        self.cli("--agent", "a", "add", "--text", "active one")
        out = self.cli_json("--agent", "a", "brief")
        self.assertEqual(set(out), {"agent", "profile", "active", "due"})
        self.assertEqual(len(out["active"]), 1)

    def test_query_adds_matches_and_dedupes_due(self):
        # one archived item is BOTH past-due and a keyword match -> appears once, under due
        self.cli("--agent", "a", "add", "--text", "acme renewal call", "--due", "2020-01-01")
        iid = self.cli_json("read")["active"][0]["id"]
        self.cli("compact", "--archive", iid)
        out = self.cli_json("--agent", "a", "brief", "--query", "acme")
        self.assertIn("matches", out)
        self.assertEqual([h["id"] for h in out["due"]], [iid])
        self.assertNotIn(iid, [h["id"] for h in out["matches"]], "due item not duplicated in matches")

    def test_agent_scope(self):
        self.cli("--agent", "a", "add", "--text", "mine")
        self.cli("--agent", "b", "add", "--text", "theirs")
        out = self.cli_json("--agent", "a", "brief")
        self.assertEqual([i["text"] for i in out["active"]], ["mine"])


class Maintenance(MemTest):
    def test_scan_flags(self):
        self.cli("--agent", "a", "add", "--text", "overdue", "--due", "2020-01-01")
        self.cli("--agent", "a", "add", "--text", "dup")
        self.cli("--agent", "a", "add", "--text", "dup")  # duplicate text
        scan = self.cli_json("scan")
        self.assertTrue(scan["overdue"])
        self.assertTrue(scan["duplicates"])

    def test_validate_fix_repairs(self):
        # write a deliberately broken memory.json (missing id + agent)
        p = os.path.join(self.root, "memory", "memory.json")
        broken = memory.empty_working()
        broken["active"] = [{"text": "no id no agent", "status": "open",
                             "people": [], "tags": []}]
        with open(p, "w", encoding="utf-8") as f:
            json.dump(broken, f)
        self.cli("validate", "--fix")
        item = self.cli_json("read")["active"][0]
        self.assertTrue(item["id"].startswith("m-"))
        self.assertEqual(item["agent"], memory.DEFAULT_AGENT)

    def test_doctor_ok_on_fresh_db(self):
        self.cli("--agent", "a", "record", "--kind", "fact", "--text", "hi")
        doc = self.cli_json("doctor")
        self.assertEqual(doc["integrity_check"], "ok")
        self.assertEqual(doc["invariant_issues"], [])
        self.assertEqual(doc["record_rows"], 1)

    def test_migration_guard_rejects_newer_schema(self):
        p = os.path.join(self.root, "memory", "memory.json")
        future = memory.empty_working()
        future["meta"]["schema_version"] = memory.SCHEMA_VERSION + 1
        with open(p, "w", encoding="utf-8") as f:
            json.dump(future, f)
        with self.assertRaises(SystemExit):
            self.cli("read")


class RichBody(MemTest):
    """goal / outcome / constraints / confidence and the `lesson` kind."""

    def test_lesson_roundtrip_and_recall_on_goal_and_constraints(self):
        self.cli("--agent", "ht", "record", "--kind", "lesson",
                 "--text", "Uploading a blog to HubSpot",
                 "--goal", "publish a draft post programmatically",
                 "--outcome", "worked via POST /cms/v3/blogs/posts",
                 "--constraints", "featured image first", "publish_date is epoch ms",
                 "--confidence", "high")
        # recall matches a term that appears ONLY in the constraints
        on_constraint = self.cli_json("recall", "--query", "epoch")["candidates"]
        self.assertEqual(len(on_constraint), 1)
        hit = on_constraint[0]
        self.assertEqual(hit["kind"], "lesson")
        self.assertEqual(hit["confidence"], "high")
        self.assertEqual(hit["constraints"],
                         ["featured image first", "publish_date is epoch ms"])
        self.assertEqual(hit["goal"], "publish a draft post programmatically")
        # and a term that appears ONLY in the goal
        self.assertTrue(self.cli_json("recall", "--query", "programmatically")["candidates"])

    def test_constraints_are_phrases_not_comma_split(self):
        # a single gotcha may contain a comma; it must stay one constraint
        self.cli("--agent", "a", "record", "--kind", "lesson", "--text", "x",
                 "--constraints", "set publish_date, in epoch ms", "second gotcha")
        hit = self.cli_json("recall", "--query", "publish_date")["candidates"][0]
        self.assertEqual(hit["constraints"], ["set publish_date, in epoch ms", "second gotcha"])

    def test_confidence_validated_and_aliased(self):
        self.cli("--agent", "a", "add", "--text", "t", "--confidence", "med")
        self.assertEqual(self.cli_json("read")["active"][0]["confidence"], "medium")
        with self.assertRaises(SystemExit):
            self.cli("--agent", "a", "record", "--kind", "fact", "--text", "y",
                     "--confidence", "superhigh")

    def test_confidence_weights_fusion(self):
        lo = self.id_by_text  # alias for brevity
        self.cli("--agent", "a", "record", "--kind", "fact", "--text", "acme one",
                 "--confidence", "low")
        self.cli("--agent", "a", "record", "--kind", "fact", "--text", "acme two",
                 "--confidence", "high")
        low_id, high_id = lo("acme one"), lo("acme two")
        ts = "2026-03-01T00:00:00+00:00"
        self.set_recorded_at(low_id, ts)
        self.set_recorded_at(high_id, ts)  # equal relevance + recency + kind -> confidence decides
        order = [h["id"] for h in self.cli_json("recall", "--query", "acme")["candidates"]]
        self.assertEqual(order[0], high_id, "high confidence outranks low, all else equal")

    def test_lesson_fields_survive_archive_and_resurface(self):
        self.cli("--agent", "a", "add", "--text", "build the thing",
                 "--goal", "ship v2", "--constraints", "needs review", "--confidence", "medium")
        iid = self.cli_json("read")["active"][0]["id"]
        self.cli("compact", "--archive", iid)
        self.cli("resurface", "--id", iid)
        item = self.cli_json("read")["active"][0]
        self.assertEqual(item["goal"], "ship v2")
        self.assertEqual(item["constraints"], ["needs review"])
        self.assertEqual(item["confidence"], "medium")

    def test_migration_from_old_schema_preserves_data_and_allows_lesson(self):
        # Build a db with the pre-2.1 schema: restrictive kind CHECK, no new columns.
        db = os.path.join(self.root, "memory", "longterm.db")
        con = sqlite3.connect(db)
        con.executescript(
            "CREATE TABLE record (id TEXT PRIMARY KEY, agent TEXT,"
            " kind TEXT NOT NULL CHECK(kind IN ('item','decision','note','fact')),"
            " type TEXT, text TEXT NOT NULL, people TEXT, tags TEXT, owner TEXT, due TEXT,"
            " status TEXT CHECK(status IN ('open','done','deferred','dropped')), source TEXT,"
            " created_at TEXT, recorded_at TEXT, reason TEXT, rationale TEXT);"
            "CREATE TABLE changelog (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT,"
            " agent TEXT, action TEXT, item_id TEXT, summary TEXT);")
        con.execute("INSERT INTO record(id,agent,kind,text,recorded_at) "
                    "VALUES('m-legacy01','old','fact','legacy fact','2026-01-01T00:00:00+00:00')")
        con.commit()
        con.close()
        # New code must migrate on connect: accept a lesson AND keep the legacy row.
        self.cli("--agent", "a", "record", "--kind", "lesson", "--text", "post-migration lesson")
        doc = self.cli_json("doctor")
        self.assertEqual(doc["integrity_check"], "ok")
        self.assertEqual(doc["invariant_issues"], [])
        self.assertEqual(doc["record_rows"], 2)
        kinds = {r["kind"] for r in self.cli_json("export")["record"]}
        self.assertEqual(kinds, {"fact", "lesson"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
