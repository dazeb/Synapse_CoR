# Update Protocol: Self-Updating In Place

## Purpose

This protocol lets Professor Synapse update **its own files** to the latest canonical release **without the user doing anything** and **without touching their personal stuff** — the `memory/` store, any custom agents they created, and the Learned Patterns they've accumulated.

Unlike the Claude-app flavor (which can't edit a skill in place and has to repackage), this portable flavor lives as plain files in a folder (`.claude/skills/`, `.codex/skills/`, `.agents/skills/`, or wherever it was dropped). That means you can fetch the new version, merge it, and **write it straight back over the install** — the user just asks you to update.

You are performing a **smart merge applied in place**, not a blind overwrite.

---

## The Canonical Source

**GitHub Repository:** `https://github.com/ProfSynapse/Professor-Synapse`
**Skill Location:** `professor-synapse-skill/` folder inside the repo

Version detection uses `releases/latest` (the tag); the actual files come from the codeload source tarball. Release *assets* (`*.githubusercontent.com`) are often proxy-blocked, so never rely on a release `.zip`/`.tar.gz` asset — `update.sh` uses codeload, which is the reliable path.

---

## What Counts as "Personal" (never overwritten)

| Personal (preserve) | Shared (update from canonical) |
|---|---|
| `memory/memory.json`, `memory/longterm.db` — everything you've remembered | `scripts/*` — `memory.py`, `summon.py`, `rebuild-index.sh`, `update.sh`, tests |
| `agents/*.md` you created that don't exist upstream — custom agents | `references/*.md` — the protocols |
| Your **Global Learned Patterns** (in `SKILL.md`) and each agent's **Learned Patterns** | `agents/domain-researcher.md`, `agents/memory-agent.md` — the base agents |
| | `SKILL.md` structure, `agents/INDEX.md` (regenerated) |

The golden rule: **update the machinery, keep the memories.** Learned Patterns live inside otherwise-shared files (`SKILL.md`, base agents), so those are merged, not blindly replaced — `update.sh` flags them for you.

---

## How to Update (the whole job)

### 1. Check whether there's anything to do

```bash
bash scripts/update.sh --check
```

Reports the local version vs. the latest release. If they match, tell the user they're current and stop.

### 2. Build the merged tree

```bash
bash scripts/update.sh            # builds /tmp/ps-update (override with --out)
#   --ref <tag|branch>   fetch a specific tag/branch (default: latest release, else main)
#   --force              rebuild even if already current
```

`update.sh` downloads the canonical codeload tarball, copies the new files into `/tmp/ps-update`, then overlays **your** `memory/` store and **your** custom agents on top. Where a shared file also holds Learned Patterns (`SKILL.md`, a base agent you've annotated), it leaves a `*.local-MERGE` copy of your version next to the canonical one and prints exactly what it preserved and what needs a hand-merge. It rebuilds `agents/INDEX.md` in the merged tree. It does **not** touch the live install — that's the next step.

### 3. Resolve any `*.local-MERGE` files (only if it flagged some)

For each `*.local-MERGE` the script reports: open it, port your Learned Patterns into the canonical file beside it in `/tmp/ps-update`, then delete the `.local-MERGE`. (A fresh install with empty pattern sections usually has nothing to merge.)

### 4. Sanity-check the carried-over store against the new code

```bash
cd /tmp/ps-update
python3 scripts/memory.py validate   # working-memory structure
python3 scripts/memory.py doctor     # long-term db integrity
```

If a release bumped the schema, migration runs automatically on first load (`memory.py` backs up to `memory.json.bak` and replaces atomically). If either command fails, stop and report — do not apply a broken tree over a good install.

### 5. Apply in place

This is the step that makes the portable flavor self-updating. The merged tree already contains your preserved memory and custom agents, so copying it over the install is safe:

```bash
cp -R /tmp/ps-update/. "<install-dir>/"     # <install-dir> = this skill's own folder
bash "<install-dir>/scripts/rebuild-index.sh"
```

`<install-dir>` is the directory this `SKILL.md` lives in. The final line of `update.sh`'s output prints these two commands with the path already filled in — run them as printed.

> **Why this is safe to do live:** `update.sh` has already exited by the time you copy, so nothing is overwriting a running script. The copy is additive over the install; if upstream *removed* a file, it lingers harmlessly until the next clean install. Never run the `cp` while `update.sh` is still going.

### 6. Verify

Run `references/self-check.md` against the now-updated install — it checks the version marker, summoning, the memory loop, and both test suites in one PASS/FAIL pass. Then tell the user what changed (summarize `references/changelog.md` for the new version).

---

## When to Use This Protocol

- The user says "check for updates" / "update yourself" / "update the skill."
- A lot of time has passed since the last check and the SKILL.md note nudges you to compare versions.
- Version detection shows a newer release than the local `**Version:**`.

The user should not have to download or move anything — running this protocol *is* the update.

---

## Safety Principles

- **Never overwrite the `memory/` store with the canonical seed.** It's the one irreplaceable thing here.
- **Never discard custom agents** (present locally, absent upstream).
- **Merge, don't clobber, Learned Patterns** — they live inside shared files; that's what the `.local-MERGE` flagging is for.
- **Show the user what changed** before and after applying.
- **Don't apply a tree that failed validation.**

---

## Fallback: doing it by hand

If `update.sh` can't run (no `bash`, or `codeload.github.com` is blocked in some environment), do the same thing manually: download `https://codeload.github.com/ProfSynapse/Professor-Synapse/tar.gz/refs/heads/main`, `tar -xzf … --strip-components=1`, take everything from the extracted `professor-synapse-skill/` **except** `memory/` and your custom agents, copy it over the install, then `bash scripts/rebuild-index.sh`. Keep your `memory/memory.json` and `memory/longterm.db` exactly as they are.

---

## Dependencies

- `curl`, `tar`, `bash` — used by `scripts/update.sh`
- `python3` — for the `memory.py` validation in step 4
