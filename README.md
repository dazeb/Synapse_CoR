# **Professor Synapse 🧙🏾‍♂️**

> **TL;DR** |
> ---
> Professor Synapse 🧙🏾‍♂️ is a wise AI guide that helps users achieve their goals by summoning expert agents perfectly suited to their tasks. It gathers context, aligns with user preferences, and creates specialized agents using a structured template to provide targeted expertise and step-by-step guidance.

## Introduction

**Professor Synapse 🧙🏾‍♂️** is a wise AI guide that helps users achieve their goals by summoning expert agents perfectly suited to their specific tasks. It gathers context about your goals, then creates and orchestrates specialized agents using a structured template to provide targeted expertise and actionable guidance.

---

## Three Ways to Use Professor Synapse

### 1. Universal Prompt (Any AI)

The classic approach — copy and paste the prompt into any AI chat interface.

**File:** `Prompt.md`

**Works with:** ChatGPT, Claude, Gemini, or any LLM that accepts system prompts.

**Setup:**
1. Open `Prompt.md` and copy the contents
2. Paste into your AI's system prompt or custom instructions
3. Start chatting!

### 2. Claude Skill (Self-Building)

A more powerful version designed for **Claude Desktop**, installed as a `.zip` you upload in Settings. This skill **grows over time** — it creates and saves expert agents for reuse, learns patterns from interactions, and maintains its own knowledge base. It includes a Claude-specific packaging workflow and versioned codeload updates.

**Folder:** `professor-synapse-claude/` (distributed as `professor-synapse-claude.zip`)

### 3. Portable Skill (Any Skills-Aware Assistant)

The same self-building skill, but **stripped of the Claude-only packaging machinery** so you can drop it straight into any assistant's skills directory — `.claude/skills/`, `.codex/skills/`, or wherever your tooling reads skills from. It's edited **in place**: new agents and memory writes take effect immediately, with nothing to repackage or reinstall. It even **updates itself in place** — ask it to check for updates and it pulls the latest release over its own files, keeping your memory and customizations.

**Folder:** `professor-synapse-skill/` (copy the folder into your skills directory)

**Both skill flavors share these features:**
- 🔎 **Domain Researcher** agent that browses the web before creating new experts
- 📚 **Self-building agent library** — created agents are saved for future sessions
- 🧠 **Persistent memory** — a shared, agent-tagged store that remembers across sessions, with ranked-fusion recall (see below)
- 💡 **Pattern learning** — captures what works and what doesn't (Global Learned Patterns in SKILL.md + per-agent patterns)
- 📋 **Auto-generated index** — agents are automatically catalogued
- 🎭 **Multi-agent debates** — convene multiple specialists for complex decisions

---

## Claude Skill Setup

### Install

1. **Download** `professor-synapse-claude.zip` from this repo

2. **Add to Claude:**
   - Open Claude → **Settings** → **Capabilities** → **Skills**
   - Click **Add new skill**
   - Upload `professor-synapse-claude.zip`

3. **Start using it:**
   - Professor Synapse activates when you say things like:
     - "Help me with..."
     - "I need guidance on..."
     - "I need an expert for..."

> 💡 Grab the latest tagged release from the [Releases page](https://github.com/ProfSynapse/Professor-Synapse/releases) for a known-good version.

### Updating

Just ask Professor Synapse to **"check for updates."** It compares its `Version:` against the latest release tag, downloads the canonical repo as a codeload tarball, and merges the update in — **preserving your custom agents, learned patterns, and `memory/` store**. It then rebuilds the skill and hands you the new package to install via "Copy to your skills." See `references/update-protocol.md` for the full mechanics.

### Skill Structure

```
professor-synapse-claude/         # (professor-synapse-skill/ is the same tree minus the ✦ files)
├── SKILL.md                      # Identity, workflow + Global Learned Patterns
├── agents/
│   ├── INDEX.md                  # Auto-generated registry
│   ├── domain-researcher.md      # Base research agent
│   └── memory-agent.md           # 🧠 Memory Keeper
├── memory/
│   ├── memory.json               # Working memory (profile + active items)
│   └── longterm.db               # SQLite long-term store + change log
├── references/
│   ├── agent-template.md         # Structure for new agents
│   ├── summon-agent-protocol.md  # How to "become" an agent
│   ├── convener-protocol.md      # Multi-agent debate facilitation
│   ├── memory-protocol.md        # How recall/capture/cleanup work
│   ├── memory-data-model.md      # Memory schema + ranked-fusion search
│   ├── domain-expertise.md       # Domain mappings
│   ├── scripts-protocol.md       # Standards for agent scripts
│   ├── self-check.md             # PASS/FAIL install verification
│   ├── changelog.md              # Version history (per-flavor — they diverge)
│   ├── update-protocol.md        # ◆ Both flavors, differ: Claude repackages; portable applies in place
│   ├── file-operations.md        # ✦ Claude-only: save/update files + packaging
│   └── rebuild-protocol.md       # ✦ Claude-only: local change rebuild workflow
└── scripts/
    ├── memory.py                 # Shared agent-tagged memory CLI
    ├── summon.py                 # Assemble an agent boot package
    ├── test_memory.py            # Memory test suite (stdlib unittest)
    ├── test_summon.py            # Summon test suite
    ├── rebuild-index.sh          # Regenerate INDEX.md
    └── update.sh                 # ◆ Both flavors, differ: Claude prepares a package; portable applies in place
```

> **✦ = Claude flavor only.** The portable `professor-synapse-skill/` flavor omits these files and the SKILL.md packaging section, since it's edited in place and needs no packaging or rebuild-to-persist step.
> **◆ = present in both, but different.** Both flavors self-update from GitHub (`update-protocol.md` + `update.sh`); the Claude flavor prepares a package the user installs via "Copy to your skills," while the portable flavor writes the merged update straight over its own files in place.

### Recommended: Claude Project Setup

For the best experience, create a dedicated Claude project for working with Professor Synapse:

1. **Create a new project** in Claude Desktop
2. **Add these project instructions:**

```
Begin the conversation with "🧙🏿‍♂️: [acknowledgment of user request]. Conjuring my professor-synapse skill to assist you."

Then follow these instructions:
1. FIRST: Use the `view` tool to check /mnt/skills/user/ for the skill
2. Read the SKILL.md file for that skill
```

**Why this helps:**
- Automatically loads the skill at conversation start
- Reads the latest SKILL.md (including any updates)
- Ensures Professor Synapse has full context from your customizations

## Portable Skill Setup

For Codex, or any assistant that loads skills from a folder:

1. **Copy** the `professor-synapse-skill/` folder into your assistant's skills directory — e.g. `.claude/skills/`, `.codex/skills/`, or wherever your tooling reads skills from. (Rename it to `professor-synapse/` if your tool keys skills by folder name.)
2. **Use it** — invoke Professor Synapse the way your assistant loads skills ("help me with…", "I need guidance on…").

Everything is edited **in place**: agents you create and memory the skill captures take effect immediately — there's nothing to repackage or reinstall.

**Updating:** just ask Professor Synapse to **"check for updates"** (or "update yourself"). It compares its `Version:` against the latest release, downloads the canonical repo as a codeload tarball, merges it, and writes the new files straight over its own folder — **preserving your `memory/` store, custom agents, and learned patterns**. You don't download or move anything; running the update *is* the update. See `references/update-protocol.md` for the mechanics.

### How the Skill Works

1. **You ask for help** → Professor Synapse greets you and gathers context
2. **Assesses complexity** → Determines if this needs one agent or multiple perspectives
3. **Path A: Single Agent** (most cases)
   - Checks `agents/INDEX.md` for a matching specialist
   - If match found → Loads and summons that agent
   - If no match → Summons 🔎 Domain Researcher to research the domain, then creates a new expert agent
4. **Path B: Convener Mode** (complex decisions)
   - Identifies multiple relevant perspectives
   - Hosts a structured debate among specialist agents
   - Synthesizes insights and presents options with trade-offs
5. **Saves new agents** → New agents are stored in `agents/` for future reuse
6. **Remembers** → Recalls relevant context at the start of work and captures new facts/decisions afterward, each tagged with the acting agent (via `scripts/memory.py`)
7. **Learns patterns** → Cross-cutting insights go in SKILL.md's Global Learned Patterns; domain-specific ones go in each agent's own Learned Patterns section

---

## Features

### Core Capabilities

+ **Expert Agent Summoning:** Creates specialized agents tailored to your specific task and domain using a structured template.
+ **Contextual Understanding:** Gathers detailed information about user goals and preferences through targeted questions.
+ **Orchestrated Conversations:** Maintains clear communication between Professor Synapse and summoned agents using a defined conversation pattern.
+ **Wise Guidance:** Provides critical yet respectful challenges to help users think deeply about their goals.
+ **Intellectual Humility:** Admits uncertainty and asks clarifying questions rather than assuming.

### Advanced Features

+ **Multi-Agent Debates (Convener Protocol):** When facing complex decisions with trade-offs, Professor Synapse can convene multiple expert agents to debate from different perspectives, then synthesize their insights into actionable recommendations.

+ **Persistent Agent-Tagged Memory:** A shared store (`scripts/memory.py`) that remembers across sessions. Every item is tagged with the agent that created it, so memory can be recalled broadly or filtered by agent. A working-memory layer (`memory.json`) holds the live profile and active items; a SQLite long-term store (`longterm.db`) holds archived decisions, notes, and facts plus a change log. The 🧠 Memory Keeper agent and the rest of the skill lean on it for recall and capture.

+ **Ranked-Fusion Recall:** `recall --query` retrieves with SQLite FTS5 (stemming, prefix, column-weighted BM25 — hits in people/tags outrank free text) and re-ranks by fusing relevance, recency, and record kind via Reciprocal Rank Fusion. A `brief` verb gives a one-shot start-of-session prefetch. No external dependencies, no embeddings — it stays fast and portable.

+ **Versioned Updates:** Each release is tagged; the skill carries a `Version:` marker and detects newer releases via `releases/latest`. The `scripts/update.sh` helper downloads the canonical repo as a single codeload source tarball, then merges it in **while preserving your custom agents, learned patterns, and — critically — your `memory/` store**, flagging only the files that need a hand-merge.

+ **Skill Rebuilding:** Easy workflow for rebuilding the skill after adding agents, scripts, or making any local changes. Uses skill-creator to package updates.

+ **Pattern Learning:** Cross-cutting insights live in SKILL.md's Global Learned Patterns; domain-specific ones live in each agent's own Learned Patterns section. The index rebuild script ensures every agent has the section.

---

## ChatGPT GPT

You can use the official Professor Synapse GPT by clicking [HERE](https://chatgpt.com/g/g-ucpsGCQHZ-professor-synapse)

If you'd like to edit and use Professor Synapse as your own GPT, follow these steps:

1. **Open ChatGPT**: Ensure you have access to OpenAI's ChatGPT.
2. **Create a GPT**: Go to the [GPT Editor](https://chatgpt.com/gpts/editor) and paste the prompt into your instructions.
3. **Edit**: Feel free to edit the prompt, but focus on the personality, name, persona if you're new to prompting.
4. **Start Interacting**: Begin a new chat and tell Professor Synapse what you want to accomplish.

---

## Interaction Flow

Professor Synapse uses a structured approach to help you achieve your goals:

1. **Introduction**: Greets you warmly and asks what you want to accomplish
2. **Context Gathering**: Asks targeted questions to understand your goals and preferences
3. **Agent Summoning**: Creates or loads an expert agent suited to your task
4. **Orchestrated Conversation**: Delegates to the expert while providing guidance
5. **Learning**: Captures patterns and insights for future interactions

---

## Contributions and Support

Feel free to explore, customize, and innovate with Professor Synapse! Please leave a ⭐ if you found this helpful.

**Support the project:** [💖 Donate](https://donate.stripe.com/bIY4gsgDo2mJ5kkfZ6)

**For more goodies:**
- 🕸 [Website](https://www.synapticlabs.ai/)
- 📺 [Youtube](https://www.youtube.com/@synapticlabs)
- 📖 [Substack](https://professorsynapse.substack.com)
