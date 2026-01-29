# **Professor Synapse 🧙🏾‍♂️**

> **TL;DR** |
> ---
> Professor Synapse 🧙🏾‍♂️ is a wise AI guide that helps users achieve their goals by summoning expert agents perfectly suited to their tasks. It gathers context, aligns with user preferences, and creates specialized agents using a structured template to provide targeted expertise and step-by-step guidance.

## Introduction

**Professor Synapse 🧙🏾‍♂️** is a wise AI guide that helps users achieve their goals by summoning expert agents perfectly suited to their specific tasks. It gathers context about your goals, then creates and orchestrates specialized agents using a structured template to provide targeted expertise and actionable guidance.

---

## Two Ways to Use Professor Synapse

### 1. Universal Prompt (Any AI)

The classic approach — copy and paste the prompt into any AI chat interface.

**File:** `Prompt.md`

**Works with:** ChatGPT, Claude, Gemini, or any LLM that accepts system prompts.

**Setup:**
1. Open `Prompt.md` and copy the contents
2. Paste into your AI's system prompt or custom instructions
3. Start chatting!

### 2. Claude Skill (Self-Building)

A more powerful version designed for Claude. This skill **grows over time** — it creates and saves expert agents for reuse, learns patterns from interactions, and maintains its own knowledge base.

**Folder:** `professor-synapse/`

**Features:**
- 🔎 **Domain Researcher** agent that browses the web before creating new experts
- 📚 **Self-building agent library** — created agents are saved for future sessions
- 🧠 **Pattern learning** — captures what works and what doesn't
- 📋 **Auto-generated index** — agents are automatically catalogued

---

## Claude Skill Setup

### Install

1. **Download** `professor-synapse.zip` from this repo

2. **Add to Claude:**
   - Open Claude → **Settings** → **Capabilities** → **Skills**
   - Click **Add new skill**
   - Upload `professor-synapse.zip`

3. **Start using it:**
   - Professor Synapse activates when you say things like:
     - "Help me with..."
     - "I need guidance on..."
     - "I need an expert for..."

### Skill Structure

```
professor-synapse/
├── SKILL.md                 # Main identity
├── agents/
│   ├── INDEX.md             # Auto-generated registry
│   └── domain-researcher.md # Base research agent
├── references/
│   ├── learned-patterns.md
│   ├── agent-template.md
│   ├── domain-expertise.md
│   └── file-operations.md
└── scripts/
    └── rebuild-index.sh
```

### How the Skill Works

1. **You ask for help** → Professor Synapse greets you and gathers context
2. **Checks existing agents** → Looks in `agents/INDEX.md` for a matching specialist
3. **Summons or creates:**
   - If match found → Loads and summons that agent
   - If no match → Summons 🔎 Domain Researcher to research the domain, then creates a new expert agent
4. **Saves new agents** → New agents are stored in `agents/` for future reuse
5. **Learns patterns** → Updates `learned-patterns.md` with what worked

---

## Features

+ **Expert Agent Summoning:** Creates specialized agents tailored to your specific task and domain using a structured template.
+ **Contextual Understanding:** Gathers detailed information about user goals and preferences through targeted questions.
+ **Orchestrated Conversations:** Maintains clear communication between Professor Synapse and summoned agents using a defined conversation pattern.
+ **Wise Guidance:** Provides critical yet respectful challenges to help users think deeply about their goals.
+ **Intellectual Humility:** Admits uncertainty and asks clarifying questions rather than assuming.

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
