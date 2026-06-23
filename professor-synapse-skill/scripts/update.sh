#!/usr/bin/env bash
# update.sh (portable flavor) - Fetch the latest Professor Synapse release and
# prepare a merged update tree, preserving the local memory/ store and custom
# agents. Unlike the Claude flavor, the portable skill is edited IN PLACE, so
# after this runs you apply the tree directly over the install dir — no
# repackaging, no "Copy to your skills" step. See references/update-protocol.md.
#
# Mechanism: downloads the canonical repo as a codeload source tarball pinned to
# the latest release tag. (github.com drives version detection via
# releases/latest; codeload.github.com serves the source tarball.)
#
# Usage:
#   bash scripts/update.sh [--check] [--ref <tag|branch>] [--out <dir>] [--force]
#     --check   report local vs latest version only; make no changes
#     --ref     fetch a specific tag or branch (default: latest release, else main)
#     --out     where to build the merged tree (default: /tmp/ps-update)
#     --force   build even if already up to date
#
# It does NOT modify the install itself. After it runs, apply the merged tree in
# place (the protocol shows the exact command) and rebuild the index.

set -euo pipefail

REPO="ProfSynapse/Professor-Synapse"
FLAVOR="professor-synapse-skill"          # the folder this flavor lives in upstream
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(dirname "$SCRIPT_DIR")"    # the skill root (wherever it was dropped)
OUT="/tmp/ps-update"
REF=""
FORCE=0
CHECK=0

note() { printf '%s\n' "$*" >&2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --ref)   REF="$2"; shift 2;;
    --out)   OUT="$2"; shift 2;;
    --force) FORCE=1; shift;;
    --check) CHECK=1; shift;;
    -h|--help) sed -n '2,20p' "$0"; exit 0;;
    *) note "unknown arg: $1"; exit 2;;
  esac
done

# --- local version (from SKILL.md "**Version:**" line) ---
LOCAL_VER="$(grep -m1 -E '^\*\*Version:\*\*' "$INSTALL_DIR/SKILL.md" 2>/dev/null \
  | sed -E 's/.*Version:\*\* *//; s/ *$//')"
[ -n "$LOCAL_VER" ] || LOCAL_VER="(none)"

# --- resolve the ref to fetch + the version it represents ---
if [ -z "$REF" ]; then
  TAG="$(curl -fsSL -o /dev/null -w '%{url_effective}' \
        "https://github.com/$REPO/releases/latest" 2>/dev/null | sed -E 's#.*/tag/##')" || TAG=""
  if [ -n "$TAG" ]; then REF="refs/tags/$TAG"; LATEST_VER="${TAG#v}"
  else note "No releases found; falling back to main."; REF="refs/heads/main"; TAG="main"; LATEST_VER="(main)"; fi
else
  case "$REF" in
    refs/*)   :;;
    v[0-9]*|[0-9]*) REF="refs/tags/$REF";;
    *)        REF="refs/heads/$REF";;
  esac
  TAG="${REF##*/}"; LATEST_VER="${TAG#v}"
fi

note "Local version:  $LOCAL_VER"
note "Latest:         $LATEST_VER  ($REF)"

if [ "$CHECK" = 1 ]; then
  if [ "$LOCAL_VER" = "$LATEST_VER" ]; then note "✓ Already up to date."
  else note "↑ Update available: $LOCAL_VER -> $LATEST_VER"; fi
  exit 0
fi

if [ "$LOCAL_VER" = "$LATEST_VER" ] && [ "$FORCE" != 1 ]; then
  note "✓ Already up to date ($LOCAL_VER). Use --force to rebuild anyway."
  exit 0
fi

# --- download + extract the canonical tarball ---
TARBALL="$(mktemp /tmp/ps-canon.XXXXXX.tar.gz)"
note "Downloading codeload tarball ($REF)…"
curl -fsSL -o "$TARBALL" "https://codeload.github.com/$REPO/tar.gz/$REF"
CANON="$(mktemp -d /tmp/ps-canon.XXXXXX)"
tar -xzf "$TARBALL" -C "$CANON" --strip-components=1
SRC="$CANON/$FLAVOR"
[ -d "$SRC" ] || { note "ERROR: extracted tree has no $FLAVOR/ dir"; exit 1; }

# --- build the merged tree (canonical, then overlay local content) ---
rm -rf "$OUT"; mkdir -p "$OUT"
cp -R "$SRC/." "$OUT/"

# 1. preserve the local memory store (USER DATA — never take the canonical seed)
PRESERVED_MEM=0
if [ -d "$INSTALL_DIR/memory" ]; then
  for f in memory.json longterm.db; do
    if [ -f "$INSTALL_DIR/memory/$f" ]; then cp -f "$INSTALL_DIR/memory/$f" "$OUT/memory/$f"; PRESERVED_MEM=1; fi
  done
fi

# 2. preserve custom agents (present locally, absent from canonical)
CUSTOM_AGENTS=()
if [ -d "$INSTALL_DIR/agents" ]; then
  for f in "$INSTALL_DIR"/agents/*.md; do
    [ -e "$f" ] || continue
    name="$(basename "$f")"
    [ "$name" = "INDEX.md" ] && continue
    if [ ! -e "$SRC/agents/$name" ]; then cp "$f" "$OUT/agents/$name"; CUSTOM_AGENTS+=("$name"); fi
  done
fi

# 3. flag files that hold local Learned Patterns for manual merge (judgment, not mechanical)
MANUAL=()
if [ -f "$INSTALL_DIR/SKILL.md" ] && ! diff -q "$INSTALL_DIR/SKILL.md" "$OUT/SKILL.md" >/dev/null 2>&1; then
  cp "$INSTALL_DIR/SKILL.md" "$OUT/SKILL.md.local-MERGE"
  MANUAL+=("SKILL.md: merge your Global Learned Patterns from SKILL.md.local-MERGE into SKILL.md, then delete the .local-MERGE file")
fi
if [ -d "$INSTALL_DIR/agents" ]; then
  for f in "$INSTALL_DIR"/agents/*.md; do
    [ -e "$f" ] || continue
    name="$(basename "$f")"
    [ "$name" = "INDEX.md" ] && continue
    if [ -e "$SRC/agents/$name" ] && ! diff -q "$f" "$OUT/agents/$name" >/dev/null 2>&1; then
      cp "$f" "$OUT/agents/$name.local-MERGE"
      MANUAL+=("agents/$name: shared agent changed; port your Learned Patterns from $name.local-MERGE, then delete it")
    fi
  done
fi

# --- rebuild the agent index ---
if ( cd "$OUT" && bash scripts/rebuild-index.sh >/dev/null 2>&1 ); then note "Rebuilt agents/INDEX.md"
else note "WARN: index rebuild failed — run 'bash scripts/rebuild-index.sh' in $OUT manually"; fi

# --- report ---
note ""
note "=== Update prepared: $OUT ==="
note "Version: $LOCAL_VER -> $LATEST_VER"
if [ "$PRESERVED_MEM" = 1 ]; then note "Preserved your memory/ store (memory.json + longterm.db)"
else note "No local memory/ store found — the canonical clean seed is included"; fi
if [ "${#CUSTOM_AGENTS[@]}" -gt 0 ]; then note "Preserved custom agents: ${CUSTOM_AGENTS[*]}"; fi
if [ "${#MANUAL[@]}" -gt 0 ]; then
  note ""
  note "MANUAL MERGE NEEDED (.local-MERGE files left in $OUT):"
  for m in "${MANUAL[@]}"; do note "  - $m"; done
fi
note ""
note "Next: resolve any merges above, then APPLY IN PLACE (this skill is edited live):"
note "  cp -R \"$OUT/.\" \"$INSTALL_DIR/\""
note "  bash \"$INSTALL_DIR/scripts/rebuild-index.sh\""
note "Your memory/ store and custom agents are already carried into $OUT, so the copy is safe."

rm -f "$TARBALL"; rm -rf "$CANON"
