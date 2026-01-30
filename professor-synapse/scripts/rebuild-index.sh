#!/bin/bash
# Rebuild INDEX.md from agent frontmatter
# Also appends learned-patterns reminder to each agent if not present
# Run from project root: bash scripts/rebuild-index.sh

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AGENTS_DIR="$PROJECT_ROOT/agents"
INDEX_FILE="$AGENTS_DIR/INDEX.md"

# Define the reminder text to append to each agent
REMINDER_TEXT="---

**REMEMBER**: One of your superpowers is that you learn over time by updating and referencing your \`learned-patterns.md\`. Review and keep this up to date regularly!"

# Start the index file
cat > "$INDEX_FILE" << 'HEADER'
# Agent Index

Auto-generated from agent frontmatter. Run `bash scripts/rebuild-index.sh` to refresh.

## Available Agents

| Agent | Emoji | Description | Triggers |
|-------|-------|-------------|----------|
HEADER

# Process each agent file (except INDEX.md)
for file in "$AGENTS_DIR"/*.md; do
    filename=$(basename "$file")

    # Skip INDEX.md itself
    if [ "$filename" = "INDEX.md" ]; then
        continue
    fi

    # Extract frontmatter fields using grep/sed
    name=$(sed -n '/^---$/,/^---$/p' "$file" | grep "^name:" | sed 's/name: *//')
    emoji=$(sed -n '/^---$/,/^---$/p' "$file" | grep "^emoji:" | sed 's/emoji: *//')
    description=$(sed -n '/^---$/,/^---$/p' "$file" | grep "^description:" | sed 's/description: *//')
    triggers=$(sed -n '/^---$/,/^---$/p' "$file" | grep "^triggers:" | sed 's/triggers: *//')

    # Add row to table
    if [ -n "$name" ]; then
        echo "| [$name]($filename) | $emoji | $description | $triggers |" >> "$INDEX_FILE"
    fi

    # Append learned-patterns reminder if not already present
    if ! grep -q "One of your superpowers is that you learn over time" "$file"; then
        echo "" >> "$file"
        echo "$REMINDER_TEXT" >> "$file"
    fi
done

echo "" >> "$INDEX_FILE"
echo "_Last updated: $(date '+%Y-%m-%d %H:%M')_" >> "$INDEX_FILE"

# Count entries (subtract header row)
ENTRY_COUNT=$(($(grep -c '^|' "$INDEX_FILE") - 1))

echo "✅ INDEX.md rebuilt with $ENTRY_COUNT agent(s)"
echo "✅ Learned-patterns reminder appended to all agents (if not already present)"
