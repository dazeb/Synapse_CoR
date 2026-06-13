# Memory Protocol

How Professor Synapse remembers across sessions. Memory is shared by all agents and tagged with the agent that created each entry, so it can be filtered by agent. Everything goes through `scripts/memory.py`; never hand-edit the store. Run `python3 scripts/memory.py --help` for verbs. For the field-by-field schema and how to version it, see `references/memory-data-model.md`.

## The store

Two files under `memory/`:

- `memory/memory.json` - working memory: a shared profile plus active items. Human-readable, hot, read often.
- `memory/longterm.db` - SQLite long-term store: archived items, decisions, notes, and facts, plus a change log. Queryable, cold.

Every active item, long-term record, and log entry carries an `agent` field. Always pass `--agent <slug>` for the agent currently acting, using the agent's `name` from its frontmatter (for example `--agent chief-of-staff`). Professor Synapse's own slug is `professor-synapse`.

## Recall (start of work)

**Fast path:** `python3 scripts/memory.py --agent <slug> brief` is the one-shot prefetch — it returns the shared profile, the agent's active items, and any long-term items now due in a single call. Add `--query <terms>` once you know the people and topics in play and it folds ranked keyword matches in too. Start here; reach for the individual verbs below when you want a narrower view.

If you'd rather surface things step by step:

1. `python3 scripts/memory.py --agent <slug> read` for that agent's active items, and `read` with no agent for the shared picture.
2. `python3 scripts/memory.py --agent <slug> recall` for long-term items whose due date has arrived.
3. Once you know the people and topics in play, `python3 scripts/memory.py recall --query <terms>` (add `--agent <slug>` to scope to one agent, omit it to search across all agents). `--query` is ranked full-text search (SQLite FTS5: stemming + prefix matching, best matches first), so terms like `renew` also surface `renewal`/`renewals`. The shared profile and other agents' facts can be relevant, so search broadly, then scope when you want one agent's view.

## Capture (during and after work)

- Working items: `add --agent <slug> --text "..." [--type ...] [--people ...] [--tags ...] [--due ...]`.
- Things born straight into long-term: `record --agent <slug> --kind decision|note|fact|lesson --text "..." [--rationale ...] [--people ...] [--tags ...]`. Use `fact` for durable things learned about the user, `decision` for choices with a rationale, `note` for context, and `lesson` for a reusable how-to learned by doing.

### Richer body (optional on any item or record)

- `--goal "..."` — what this is in service of (the objective).
- `--outcome "..."` — what resulted / the current state.
- `--constraints "gotcha one" "gotcha two"` — limits and gotchas. Each is a **quoted phrase** (a constraint may itself contain a comma), not a comma-list.
- `--confidence high|medium|low` — how sure you are; nudges recall ranking. Best on `fact`s that might decay.

A `lesson` shines when it carries all four: e.g. `record --kind lesson --text "Upload a blog to HubSpot" --goal "publish a draft via API" --outcome "POST /cms/v3/blogs/posts works" --constraints "upload featured image first" "publish_date is epoch ms" --confidence high`. `goal`, `outcome`, and `constraints` are all full-text searchable, so a later `recall --query "hubspot epoch"` surfaces the gotcha directly.

Always fill `--people` and `--tags`; they power recall. Tag with the acting agent so the entry can be filtered later. Short list options accept either form — `--tags a b` or `--tags a,b` both store two distinct tags (constraints are the exception: always quote each phrase).

## Janitor (keep it from going stale)

`python3 scripts/memory.py scan` (optionally `--agent <slug>`) returns overdue, done, stale, and duplicate candidates. Add judgment a script cannot, then propose a short maintenance list and let the user approve. Apply with `compact --archive <ids>` or `--drop <ids> --reason "..."`. Resurface a parked item with `resurface --id <id>` (it returns under its original id and agent).

## Filtering by agent

`--agent <slug>` filters reads and scopes recall, scan, export, and render. The `agents` verb lists every agent that has touched memory with active and long-term counts. Omit `--agent` on a read to see the whole landscape.

## Persisting (important)

This store lives inside the Professor Synapse skill, so a memory change only survives if the skill is rebuilt and reinstalled. Follow `references/rebuild-protocol.md`. Because that rebuilds the whole skill, batch your writes and rebuild once at the end of a session rather than after every entry. If code execution is off, you cannot rebuild; tell the user and offer the updated memory as text (`render`).

## Integrity

Writes to `memory.json` validate, back up to `memory.json.bak`, and replace atomically, so a bad write cannot land. If `read` reports trouble, run `validate --fix` (safe mechanical repairs only) and `doctor` for the db.
