#!/usr/bin/env bash
# Rebuild a MERGED agents/INDEX.md from agent frontmatter across both roots:
#   - built-in agents shipped with the skill (read-only in a plugin)
#   - user-created agents in the writable data dir (survive plugin updates)
# The merged index is written to the WRITABLE data agents dir. Learned-Patterns
# sections are ensured only on writable (user) agent files; shipped agents already
# carry theirs and the install dir is read-only.
#
# Note: routing does NOT depend on this file — `summon.py --list` is the canonical,
# always-current roster. INDEX.md is a human-readable convenience.

set -euo pipefail

show_help() {
    cat << 'EOF'
USAGE
  bash scripts/rebuild-index.sh [options]

DESCRIPTION
  Regenerates a merged agents/INDEX.md (built-in + user agents) in the writable
  data dir, and ensures each USER agent file has a Learned Patterns section.

OPTIONS
  -h, --help   Show this help message

NOTES
  Run from anywhere; paths are resolved from the script location. In a plugin the
  index lands in the persistent data dir; in-place it lands beside the agents.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_help; exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"
BUILTIN_AGENTS="$SKILL_ROOT/agents"

# Resolve the writable data root (plugin data dir, or the skill root in-place).
DATA_ROOT="$(python3 "$SCRIPT_DIR/_pluginpaths.py" "$SKILL_ROOT" 2>/dev/null || echo "$SKILL_ROOT")"
USER_AGENTS="$DATA_ROOT/agents"
mkdir -p "$USER_AGENTS"
INDEX_FILE="$USER_AGENTS/INDEX.md"

LEARNED_PATTERNS_SECTION='## Learned Patterns

### Effective Patterns
<!-- Domain-specific patterns that work well for this agent. Add entries as you learn. -->

### Anti-Patterns
<!-- Domain-specific mistakes to avoid for this agent. Add entries as you learn. -->'

REMINDER_TEXT='---

**REMEMBER**: You learn over time! Update SKILL.md'"'"'s **Global Learned Patterns** for cross-cutting insights and this agent'"'"'s **Learned Patterns** section above for domain-specific insights.'

# Header
cat > "$INDEX_FILE" << 'HEADER'
# Agent Index

Auto-generated (merged built-in + user agents) from agent frontmatter.
Run `bash scripts/rebuild-index.sh` to refresh. Routing uses `summon.py --list`.

## Available Agents

| Agent | Emoji | Description | Triggers |
|-------|-------|-------------|----------|
HEADER

emit_rows() {
    local dir="$1" writable="$2"
    [ -d "$dir" ] || return 0
    for file in "$dir"/*.md; do
        [ -e "$file" ] || continue
        local filename; filename="$(basename "$file")"
        [ "$filename" = "INDEX.md" ] && continue
        local fm name emoji description triggers
        fm="$(sed -n '/^---$/,/^---$/p' "$file")"
        name="$(printf '%s\n' "$fm" | grep '^name:' | head -1 | sed 's/name: *//')"
        emoji="$(printf '%s\n' "$fm" | grep '^emoji:' | head -1 | sed 's/emoji: *//' | tr -d '"')"
        description="$(printf '%s\n' "$fm" | grep '^description:' | head -1 | sed 's/description: *//')"
        triggers="$(printf '%s\n' "$fm" | grep '^triggers:' | head -1 | sed 's/triggers: *//')"
        [ -n "$name" ] && echo "| [$name]($filename) | $emoji | $description | $triggers |" >> "$INDEX_FILE"
        # Ensure Learned Patterns on writable (user) agents only.
        if [ "$writable" = "yes" ] && ! grep -q '^## Learned Patterns' "$file"; then
            { echo ""; echo "$LEARNED_PATTERNS_SECTION"; echo ""; echo "$REMINDER_TEXT"; } >> "$file"
            echo "  + Learned Patterns added to $filename"
        fi
    done
}

emit_rows "$BUILTIN_AGENTS" "no"
if [ "$(cd "$USER_AGENTS" && pwd)" != "$(cd "$BUILTIN_AGENTS" && pwd)" ]; then
    emit_rows "$USER_AGENTS" "yes"
fi

echo "" >> "$INDEX_FILE"
echo "_Last updated: $(date '+%Y-%m-%d %H:%M')_" >> "$INDEX_FILE"

ENTRY_COUNT=$(( $(grep -c '^|' "$INDEX_FILE") - 1 ))
echo "✅ INDEX.md rebuilt with $ENTRY_COUNT agent(s) -> $INDEX_FILE"
