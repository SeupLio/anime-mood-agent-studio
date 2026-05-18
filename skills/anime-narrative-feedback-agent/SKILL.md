---
name: anime-narrative-feedback-agent
description: Use when designing anime mobile game agents that interpret story, character, CG, event, PV, or fandom feedback and convert emotional reactions into narrative hooks, content insights, dialogue strategies, and writer-facing recommendations.
---

# Anime Narrative Feedback Agent

Use this skill to turn player emotional reactions into narrative and content-design insight.

## Inputs

- Player comments about story, character, relationship, event, voice, CG, PV, or ending.
- Emotion fusion output from text, image, or video.
- Optional context: character name, chapter, event, spoiler boundary, release stage.

## Workflow

1. Identify content target.
   - Character, relationship, plot beat, event mechanic, art direction, voice, music, pacing, or ending.

2. Separate emotion from preference.
   - Emotion: what the player feels.
   - Preference: what the player wants changed or repeated.
   - Fandom signal: meme, ship, nickname, ritual phrase, or community expectation.

3. Map emotion to narrative action.
   - `joy`: preserve high-light tags, identify repeatable charm.
   - `anticipation`: build teaser hooks and future-facing questions.
   - `sadness`: create companionship, closure, or recovery beats.
   - `fear`: reduce uncertainty or make tension intentional.
   - `anger`: identify broken expectation, perceived betrayal, or pacing mismatch.
   - `surprise`: distinguish delightful twist from confusing twist.

4. Produce agent behavior.
   - Player reply: acknowledge feeling without spoiling.
   - Writer insight: summarize what worked or failed.
   - Operations insight: flag whether the reaction is content-positive, confused, or risky.

5. Respect spoiler boundaries.
   - Ask for release stage if it changes what can be said.
   - Avoid revealing future plot, unreleased character information, or hidden mechanics.

## Output Pattern

Return:

- Content target.
- Emotional reading.
- Player-facing response.
- Writer-facing insight.
- Suggested narrative hook or follow-up question.
- Spoiler or uncertainty notes.

## Guardrails

- Do not fabricate lore.
- Do not canonize player theories.
- Do not over-index on one loud reaction; recommend clustering when impact is uncertain.
