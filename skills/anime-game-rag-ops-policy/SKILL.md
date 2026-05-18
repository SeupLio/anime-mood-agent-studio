---
name: anime-game-rag-ops-policy
description: Use when building or improving RAG-backed anime mobile game agents for maintenance compensation, gacha rules, event policy, customer support wording, community response, and citation-grounded player answers.
---

# Anime Game RAG Ops Policy

Use this skill when an agent must answer player or operator questions from game policy knowledge.

## Knowledge Scope

Useful source documents include:

- Maintenance and compensation rules.
- Gacha probability, pity, banner, paid currency, and refund policy.
- Event participation, rewards, time windows, and bug handling.
- Customer support macros.
- Community escalation and public announcement guidance.
- Story, character, and spoiler-response rules.

## Workflow

1. Classify the question.
   - Determine whether it is about compensation, gacha, event rules, support wording, community risk, or narrative feedback.

2. Retrieve narrowly.
   - Prefer exact keywords, game terms, banner names, version numbers, and Chinese bigrams for lightweight retrieval.
   - For vector retrieval, keep metadata filters for version, event, channel, and policy type.

3. Answer with citations.
   - Summarize only what retrieved policy supports.
   - Include citations with source title, section, and chunk id when available.
   - State uncertainty when the retrieved chunks are insufficient.

4. Adapt to audience.
   - Player answer: concise, empathetic, no internal process details.
   - Support macro: repeatable wording, required data fields, escalation condition.
   - Operator answer: include risk, dependencies, and suggested next action.

5. Feed back into the agent.
   - Pass policy constraints to the response planner.
   - Block unsupported promises.
   - Mark missing policy as a content gap for LiveOps.

## Output Pattern

Return:

- Short answer.
- Citations.
- Confidence or coverage note.
- Recommended support or operations action.

## Guardrails

- Do not invent compensation, drop rates, legal terms, or release timing.
- Do not expose internal-only instructions to players.
- If policies conflict, surface the conflict and recommend human review.
