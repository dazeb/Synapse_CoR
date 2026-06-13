# Memory Data Model

The canonical reference for Professor Synapse's shared memory. Read before changing the schema or the CLI. All access goes through `scripts/memory.py`; nothing hand-edits the files.

## Principle: cheap versus expensive change

- **Cheap, anytime:** an optional field (a JSON key with a default, or a db column via `ALTER TABLE ADD COLUMN`). Read it with a default and old data still works.
- **Expensive, needs a migration:** renaming a field, changing its type, splitting one into several, or changing an enum's meaning.
- **Impossible to backfill:** data never captured. This is why `agent`, `people`, and `tags` are structured from the start.

## The agent dimension

Every active item, long-term record, and changelog row carries an `agent` slug: the agent that created it. This is what lets memory be filtered by agent. Slugs match each agent's frontmatter `name`. Professor Synapse itself uses `professor-synapse`.

## Stores

- `memory/memory.json` - working memory (shared profile + active items). Hot.
- `memory/longterm.db` - long-term records and a change log. Cold.

## Invariants

- Each item has one opaque id (`m-` plus 8 hex) for life.
- An id is active in `memory.json` or archived in `longterm.db`, never both. `resurface` moves it back under the same id and agent.
- Active-item and long-term-record field names match for shared columns, so archiving is a copy.
- Working-memory writes validate, back up to `memory.json.bak`, then atomically replace.

## memory.json

### meta
| field | type | notes |
|---|---|---|
| `schema_version` | int | migration anchor. Currently 1. |
| `updated_at` | UTC ISO datetime | set on every write |

### profile (shared across agents, person-level)
| field | type | notes |
|---|---|---|
| `name`, `title`, `notes` | string or null | |
| `focus_areas` | list of strings | |
| `key_people` | list of `{name, role, note}` | |

### active item
| field | type | notes |
|---|---|---|
| `id` | string `m-<8 hex>` | opaque, lifelong, unique across both stores |
| `agent` | string | the agent that owns it; powers filtering |
| `type` | string or null | free-form sub-type the agent defines (no fixed enum) |
| `text` | string | |
| `people` | list of strings | powers recall |
| `tags` | list of strings | powers recall |
| `owner` | string or null | |
| `due` | date `YYYY-MM-DD` or null | |
| `status` | enum: `open`, `done` | |
| `source` | string or null | |
| `goal` | string or null | what the item is in service of |
| `outcome` | string or null | what resulted / current state |
| `constraints` | list of strings | gotchas/limits; each is a phrase (not comma-split), powers recall |
| `confidence` | enum or null: `high`, `medium`, `low` | how sure; nudges recall fusion |
| `created_at`, `updated_at` | date `YYYY-MM-DD` | |

## longterm.db

### record (archived item, decision, note, fact, or lesson; keyed by lifelong id)
| column | type | notes |
|---|---|---|
| `id` | TEXT PK | same id as when active |
| `agent` | TEXT | who created it |
| `kind` | TEXT NOT NULL: `item`,`decision`,`note`,`fact`,`lesson` | discriminator. Validated in Python (`RECORD_KINDS`), **not** a DB CHECK, so new kinds need no table rebuild |
| `type` | TEXT | free-form sub-type |
| `text` | TEXT NOT NULL | the core memory / headline |
| `people`, `tags` | TEXT (JSON array string) | |
| `owner` | TEXT | |
| `due` | TEXT (date) | |
| `status` | TEXT, in (`open`,`done`,`deferred`,`dropped`) | (still a DB CHECK) |
| `source` | TEXT | |
| `created_at` | TEXT (date) | |
| `recorded_at` | TEXT (UTC datetime) | when it entered long-term |
| `reason` | TEXT | why archived/dropped |
| `rationale` | TEXT | for decisions, why decided |
| `goal` | TEXT | what was being attempted (esp. `lesson`) |
| `outcome` | TEXT | what resulted (esp. `lesson`) |
| `constraints` | TEXT (JSON array string) | gotchas/limits; each a phrase |
| `confidence` | TEXT: `high`/`medium`/`low` | how sure (esp. `fact`) |

The `lesson` kind is a reusable how-to learned by doing — it conventionally fills `goal`, `outcome`, and `constraints`, but those fields are optional on every kind. `goal`/`outcome`/`constraints` are full-text indexed for recall; `confidence` and `kind` apply multiplicative nudges in fusion.

### changelog (append-only audit)
| column | type | notes |
|---|---|---|
| `seq` | INTEGER PK AUTOINCREMENT | |
| `ts` | TEXT (UTC datetime) | |
| `agent` | TEXT | who acted |
| `action` | TEXT | `archive`, `drop`, `resurface`, `decision`, `note`, `fact` |
| `item_id` | TEXT | |
| `summary` | TEXT | |

## Tunable constants

Near the top of `scripts/memory.py`: `SCHEMA_VERSION`, `STALE_DAYS` (21), `LOG_CAP_DAYS` (90), `DEFAULT_AGENT`, and the recall-fusion knobs `RRF_K` (60), `W_TEXT` (1.0), `W_RECENCY` (0.5), `BM25_WEIGHTS` (id/text/people/tags/owner/goal/outcome/constraints — 8 columns), `KIND_WEIGHT` (includes `lesson`), and `CONFIDENCE_WEIGHT` (`high`/`medium`/`low` multipliers).

## Adding a field, a column, or a version

- Working-memory field: add it to `empty_working()` with a default and read it defensively. No migration needed if purely additive.
- Db column: add it to `RECORD_DDL` and to `RECORD_COLUMNS`, then add an idempotent guard in `_migrate_record_schema()` (the loop that runs `ALTER TABLE record ADD COLUMN ...` when a column is missing). Existing dbs upgrade in place on the next `connect_db()`.
- New `kind` value: add it to `RECORD_KINDS` (and `KIND_WEIGHT` if it should rank distinctly). Because `kind` is validated in Python rather than by a DB CHECK, no rebuild is needed for *new* dbs. For dbs created before that change, `_migrate_record_schema()` detects the old restrictive `CHECK(kind IN (...))` in the stored DDL and **rebuilds the `record` table once** (rename → recreate from `RECORD_DDL` → copy all rows → drop old), preserving every row. This ran for the `lesson` addition.
- Working-memory breaking change: bump `SCHEMA_VERSION` and register a transform in `MIGRATIONS` keyed by the version you migrate FROM. `migrate_working` runs it on load, refuses if a step is missing, and refuses files newer than the skill, so a mismatch fails loud.

## Search: ranked fusion over full-text, no extra storage

`recall --query` and `brief --query` are a two-stage ranker:

1. **Retrieve** with **SQLite FTS5** (stemming + prefix matching). The index is **built transiently at query time** from the `record` table and dropped immediately — no persistent FTS table, no triggers, **no schema change or migration**. Retrieval uses **column-weighted BM25** (`BM25_WEIGHTS`) over `text/people/tags/owner/goal/outcome/constraints` so a hit in `people`/`tags`/`constraints` outranks one buried in free text, and `goal`/`outcome` rank above plain text. It pulls a candidate pool (≈3× the result limit).
2. **Re-rank** the pool by **fusing signals** with Reciprocal Rank Fusion (RRF): the BM25 relevance order (`W_TEXT`) and the recency order by `recorded_at` (`W_RECENCY`, a secondary nudge so a strongly-relevant old fact still wins), then multiplicative nudges — `KIND_WEIGHT` so `fact`/`lesson`/`decision` edge out `note`, and `CONFIDENCE_WEIGHT` so a `high`-confidence record edges out a `low` one. `dropped` records are excluded — they were retired on purpose.

RRF is scale-free, so the disparate signals combine without normalizing raw scores. At this store's scale (tens to low hundreds of records) the whole thing is instant and needs zero maintenance. If a SQLite build lacks FTS5, `recall` falls back to substring `LIKE`, so it is never worse than before.

Semantic/vector search (e.g. `sqlite-vec` + embeddings) was considered and **rejected as overkill**: it needs a loadable extension (often disabled in the sandbox's `sqlite3`) plus vendored model weights, for gains that aren't perceptible at this scale — and the LLM driving the skill already supplies the semantic layer (it can issue synonym queries itself). Revisit only if the store grows by orders of magnitude.

## Deferred on purpose

`people` and `tags` are JSON arrays in a TEXT column, not a junction table. FTS5 (and `LIKE` as a fallback) over the joined values is enough at this scale. Migrating to a `record_people` junction table later is possible by parsing the JSON; reach for it only when simple search stops being enough.
