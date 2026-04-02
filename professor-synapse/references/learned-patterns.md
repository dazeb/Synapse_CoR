# Global Learned Patterns & Anti-Patterns

This file is for **cross-cutting patterns that apply across ALL agents** (professor-level). Domain-specific patterns belong in each agent's own **Learned Patterns** section at the end of its file.

**Where does this pattern belong?**
- **Here (global)**: Applies to multiple agents or to Professor Synapse's general behavior. Example: "Always ask about user's background before diving in."
- **Agent file (domain-specific)**: Applies only to one agent's domain. Example: "For ML users, start with decision trees for interpretability."

## How to Use This File

1. Check here FIRST before creating new agents
2. Match by context: Look for patterns matching user's domain + level + task type
3. Check anti-patterns: Avoid known failure modes
4. Adapt existing: If close match, adapt rather than create from scratch
5. Update after interactions: Add both successes AND failures
6. Also check individual agent files for domain-specific patterns

## How to Update This File

> **CRITICAL**: After updating this file, you MUST complete the full skill packaging workflow. See `file-operations.md` section "How to Update Learned Patterns" for the required steps. Claude Desktop cannot edit skills in place - changes are lost without the packaging workflow.

### Adding a Pattern (what worked)

Template:
```
### [Pattern Name]
**Triggers**: [keywords, user level, task type]
**Effective Config**:
- Emoji: [emoji]
- Title: [title]
- Techniques: [what worked]
- Style: [communication approach]

**What Worked**:
- [Specific effective approach]
- [Question that clarified well]
```

### Adding an Anti-Pattern (what to avoid)

Template:
```
### [Anti-Pattern Name]
**Triggers**: [when this mistake tends to happen]
**The Mistake**: [what went wrong]
**Why It Failed**: [root cause]
**Instead Do**: [correct approach]
```

---

## Effective Patterns

### ML for Business Users
> **Migration note**: This is a domain-specific pattern. When an ML agent is created, move this into that agent's **Learned Patterns** section and remove it from here.

**Triggers**: machine learning, prediction, business stakeholder, interpretability
**Effective Config**:
- Emoji: 🤖
- Title: ML Business Translator
- Techniques: Decision trees, SHAP, confusion matrix as "false alarms vs misses"
- Style: No jargon, business analogies, ROI framing

**What Worked**:
- Start with "what decision will this inform?" before technical work
- Decision tree first (interpretable baseline)
- Frame metrics in business terms

---

## Anti-Patterns (What to Avoid)

### ⚠️ Assuming Technical Expertise
**Triggers**: User asks about ML/data without specifying background
**The Mistake**: Jumping into technical jargon, assuming familiarity with concepts
**Why It Failed**: User felt lost, couldn't follow, disengaged
**Instead Do**: Ask about their background first, calibrate language accordingly

### ⚠️ Solutioning Before Understanding
**Triggers**: User describes a problem, seems urgent
**The Mistake**: Immediately proposing solutions before gathering full context
**Why It Failed**: Solved the wrong problem, wasted effort
**Instead Do**: Ask 2-3 clarifying questions even when answer seems obvious
