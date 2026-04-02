# Changelog

Version history for the Professor Synapse skill. Check this after fetching updates to see what changed.

---

## 2026-04-02

- **GitHub blob parser fix**: Updated `github_blob_parser.py` to handle GitHub's reorganized JSON payload structure (`payload.codeViewBlobRoute.richText` and `payload['codeViewBlobLayoutRoute.StyledBlob'].rawLines`), with fallback to legacy paths
- **Packaging workflow enforcement**: Added mandatory packaging workflow section to SKILL.md — impossible to miss
- **Two-tier learned patterns**: Global patterns now live directly in SKILL.md; domain-specific patterns live in each agent's own Learned Patterns section
- **Agent template updated**: Learned Patterns section (Effective Patterns / Anti-Patterns) added to agent template with format templates
- **rebuild-index.sh**: Auto-appends Learned Patterns section to any agent file missing it
- **Removed `references/learned-patterns.md`**: Content moved into SKILL.md's Global Learned Patterns section
- **Changelog added**: This file — tracks version changes for the update protocol

## 2026-01-30

- Initial release with domain researcher agent, convener protocol, and update/rebuild protocols
