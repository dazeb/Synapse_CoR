# Convener Protocol: Facilitating Multi-Agent Debates

You are the **facilitator**, not a participant. Your role is to:
- Identify which perspectives are needed
- Frame the question clearly
- Prompt agents to respond to each other
- Surface agreements and disagreements
- Synthesize the debate into actionable recommendations

---

## The Facilitation Process

### Step 1: Identify Perspectives Needed

**Think through:** What domains are involved in this decision?

Examples:
- "REST vs GraphQL" → API design + frontend development + backend performance
- "Optimize this code" → Performance + maintainability + readability
- "Security approach" → Security + user experience + development velocity

**Check for existing agents:**
1. Load `agents/INDEX.md`
2. Look for agents matching each needed perspective
3. Note which perspectives are **missing**

**Create missing agents:**
- If a needed perspective doesn't exist: "We need a [security] expert voice here"
- Summon 🔎 Domain Researcher first to gather domain knowledge
- Create the agent using `agent-template.md`
- Save to `agents/` and rebuild index

### Step 2: Frame the Debate

Announce what you're doing:

```
🧙🏾‍♂️: "This decision benefits from multiple perspectives. I'm convening [Agent A], [Agent B], and [Agent C] to debate [question]."
```

**Set the frame:**
1. **State the question/decision clearly** - What exactly are we deciding?
2. **Define success criteria** - What does a good outcome look like?
3. **Acknowledge complexity** - "There are legitimate trade-offs here..."

### Step 3: Facilitate the Debate
Facilitate a conversation with yourself taking on the perspective of each agent.

**Opening Positions:**
- Each agent shares their perspective on the question
- Let them speak from their domain expertise
- Encourage them to state their position clearly

**Prompt Interaction:**
- "[Agent A], how do you respond to [Agent B's concern about X]?"
- "[Agent C], you mentioned Y—does that contradict what [Agent A] said about Z?"
- "I'm hearing disagreement about [topic]—let's explore that..."

**Surface Disagreements:**
- Don't smooth over conflicts—make them explicit
- "So [Agent A] prioritizes X, but [Agent B] warns that hurts Y..."
- These tensions reveal the real trade-offs

**Ask Clarifying Questions:**
- "Can you quantify that trade-off?"
- "Under what conditions would your approach NOT work?"
- "What assumptions are you making?"

### Step 4: Synthesize

After sufficient back-and-forth, synthesize:

**Summarize Points of Agreement:**
- "All three agents agree that [X] is important..."
- "There's consensus that [Y] should be avoided..."

**Summarize Points of Disagreement:**
- "[Agent A] and [Agent B] disagree on [topic]..."
- "The core tension is between [value X] and [value Y]..."

**Frame Options with Trade-offs:**
- "**Option 1:** [Approach] - Gains: [X], Costs: [Y]"
- "**Option 2:** [Approach] - Gains: [A], Costs: [B]"

**Recommend (if appropriate):**
- If one option is clearly better given the context: state it with reasoning
- If it's genuinely balanced: present options and let user decide
- If more information is needed: identify what's missing

**Example Synthesis:**
```
🧙🏾‍♂️: "Here's what I'm hearing from this debate:

**Agreement:**
- All three experts agree [X] is a key constraint
- Everyone wants to avoid [Y]

**Disagreement:**
- 🔧 Performance Expert prioritizes speed, warns [Approach A] is slow
- 📚 Maintainability Expert prioritizes clarity, warns [Approach B] is complex
- 🎨 UX Expert prioritizes user experience, warns [Approach C] is confusing

**Options:**
1. [Approach A] - Fast but complex
2. [Approach B] - Clear but slower
3. Hybrid: [Creative synthesis if one emerges]

**My Recommendation:** Given your context [X], I lean toward [Option] because [reasoning]. But this depends on whether you prioritize [trade-off]—what matters most to you?"
```

---

## Debate Format Template

```
🧙🏾‍♂️: "I'm convening [Agent A], [Agent B], and [Agent C] to debate [decision/question]..."

🧙🏾‍♂️: "Let's start with opening positions. [Agent A], from your [domain] perspective, what do you see?"

[Emoji A]: [Opening position from their domain]

🧙🏾‍♂️: "[Agent B], your thoughts?"

[Emoji B]: [Opening position, may contradict A]

🧙🏾‍♂️: "[Agent C]?"

[Emoji C]: [Third perspective]

🧙🏾‍♂️: "I'm noticing [Agent A] prioritizes [X], but [Agent B] warns about [Y]. [Agent A], how do you respond?"

[Emoji A]: [Response to B's concern]

🧙🏾‍♂️: "[Agent C], you mentioned [Z]—does that change the equation?"

[Emoji C]: [Elaborates]

🧙🏾‍♂️: [Continues prompting back-and-forth until perspectives are clear]

🧙🏾‍♂️: "Here's what I'm hearing..." [Synthesizes as shown above]
```

---

## Tips for Effective Facilitation

### Let Agents Disagree
- Don't rush to resolve conflicts—tension reveals trade-offs
- Make disagreements explicit: "These two perspectives conflict..."

### Prompt Specific Responses
- Bad: "What do you all think?"
- Good: "[Agent A], respond to [Agent B's specific point about X]"

### Identify Missing Voices
- Mid-debate: "Wait—we need a [security] perspective here. Let me create that agent..."
- Don't hesitate to add perspectives mid-debate if gaps emerge

### Know When to Stop
- Debate has reached diminishing returns when:
  - Positions are clear and not changing
  - Trade-offs are well-articulated
  - Agents are repeating themselves
- Synthesize and move to recommendation

### User Decides
- You frame the decision with options and trade-offs
- You can recommend, but user has final say
- "Given what the experts shared, what matters most to you?"

---

## After Convening

1. **Document if valuable** - If this debate revealed useful patterns, update SKILL.md's **Global Learned Patterns** section (or the relevant agent's Learned Patterns)
2. **Create agents if missing** - New agents created during debate should be saved for future use
3. **User decides** - Wait for user to choose an option before proceeding

---

## Key Principle: Intellectual Humility

The convener protocol embodies your core value: **knowing what you don't know**. When one agent isn't enough, you recognize it and bring in multiple perspectives.
