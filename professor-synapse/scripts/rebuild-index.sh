#!/bin/bash
# Rebuild INDEX.md from agent frontmatter
# Run from project root: bash scripts/rebuild-index.sh

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AGENTS_DIR="$PROJECT_ROOT/agents"
INDEX_FILE="$AGENTS_DIR/INDEX.md"

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
done

echo "" >> "$INDEX_FILE"
echo "_Last updated: $(date '+%Y-%m-%d %H:%M')_" >> "$INDEX_FILE"

echo "INDEX.md rebuilt with $(grep -c '^|' "$INDEX_FILE") entries"
