#!/bin/bash
# Package the Claude flavor of the Professor Synapse skill for Claude Desktop.
# Run from project root: bash scripts/package-skill.sh
#
# Only the Claude flavor (professor-synapse-claude/) is zipped for upload. The
# portable flavor (professor-synapse-skill/) is distributed as a plain folder
# you drop into your assistant's skills directory — it needs no packaging.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SKILL_DIR="$PROJECT_ROOT/professor-synapse-claude"
OUTPUT_FILE="$PROJECT_ROOT/professor-synapse-claude.zip"

# Ensure we're in the right place
if [ ! -d "$SKILL_DIR" ]; then
    echo "Error: professor-synapse-claude/ folder not found"
    echo "Run this script from the Professor-Synapse project root"
    exit 1
fi

# Rebuild the agent index first
echo "Rebuilding agent index..."
if [ -f "$SKILL_DIR/scripts/rebuild-index.sh" ]; then
    bash "$SKILL_DIR/scripts/rebuild-index.sh"
fi

# Remove old zip if exists
if [ -f "$OUTPUT_FILE" ]; then
    rm "$OUTPUT_FILE"
fi

# Create the zip
echo "Creating professor-synapse-claude.zip..."
cd "$PROJECT_ROOT"
zip -r professor-synapse-claude.zip professor-synapse-claude/ \
    -x "professor-synapse-claude/.DS_Store" \
    -x "professor-synapse-claude/**/.DS_Store" \
    -x "professor-synapse-claude/**/*.pyc" \
    -x "professor-synapse-claude/**/__pycache__/*" \
    -x "professor-synapse-claude/**/*.bak" \
    -x "professor-synapse-claude/memory/memory.json.bak"

echo ""
echo "✅ Created: $OUTPUT_FILE"
echo ""
echo "To install in Claude:"
echo "  1. Open Claude → Settings → Capabilities → Skills"
echo "  2. Click 'Add new skill'"
echo "  3. Upload professor-synapse-claude.zip"
