---
name: anime-player-memory-personalization
description: Use when designing deeper anime mobile game agents that maintain player preference memory, relationship context, persona consistency, recommendation signals, retention interventions, and safe personalization loops.
---

# Anime Player Memory Personalization

Use this skill for deeper agent systems that adapt to a player across sessions without becoming invasive or manipulative.

## Memory Types

Store only task-useful and consent-compatible signals:

- Preference memory: favorite characters, story themes, art style, preferred challenge level.
- Interaction memory: unresolved support issue, previous complaint, selected archetype, known confusion.
- Progress context: current version, event participation, broad progression stage.
- Negative constraints: disliked content, spoiler sensitivity, opt-out flags.

Avoid storing sensitive personal data unless the product has explicit policy, consent, and deletion flows.

## Workflow

1. Define the personalization goal.
   - Support continuity, content recommendation, onboarding, retention recovery, story recap, or companion dialogue.

2. Decide what memory is necessary.
   - Keep a short memory schema.
   - Record evidence and timestamp.
   - Prefer interpretable labels over raw chat logs when possible.

3. Read memory conservatively.
   - Use memory to reduce repeated questions and improve relevance.
   - Do not let memory override the latest user request.
   - When confidence is low, phrase as a question rather than a fact.

4. Update memory.
   - Write only durable preferences or unresolved state.
   - Decay temporary emotions and event-specific reactions.
   - Preserve opt-out and safety constraints.

5. Plan agent action.
   - Personalize tone, recommendations, recap, or support next step.
   - Keep business goals secondary to player trust.

## Output Pattern

Return:

- Memory read summary.
- New memory candidates with evidence.
- Action plan influenced by memory.
- Privacy or consent note if needed.

## Guardrails

- Do not infer real-world identity, age, finances, mental health, or relationships from gameplay text.
- Do not use memory to pressure spending.
- Provide a path to forget, reset, or ignore personalization when designing product flows.
