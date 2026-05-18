---
name: anime-game-emotion-fusion
description: Use when building, reviewing, or extending multimodal emotion intelligence for anime mobile games, especially player text, character or event images, PV frames, semantic contrast, confidence weighted fusion, and explainable emotion vectors.
---

# Anime Game Emotion Fusion

Use this skill to turn anime-game player content into explainable emotion signals that can drive agent decisions.

## Inputs

- Player text: feedback, customer support messages, community comments, story reactions.
- Visual content: character art, event key visuals, battle screenshots, CGs, PV frames.
- Optional context: version, event, channel, player segment, known issue, monetization state.

## Workflow

1. Normalize the task.
   - Identify whether the user needs analysis, feature design, evaluation, or code changes.
   - Keep the output tied to game operations, support, narrative, or content validation.

2. Extract text emotion.
   - Use the same emotion space across modules: `joy`, `sadness`, `anger`, `fear`, `trust`, `surprise`, `anticipation`, `disgust`, `neutral`.
   - Return `valence`, `arousal`, `confidence`, evidence terms, and a short explanation.
   - Treat negation, intensifiers, sarcasm clues, emoji, and fandom slang as first-class evidence.

3. Extract visual mood.
   - For lightweight environments, use interpretable visual features such as brightness, saturation, contrast, warmth, coolness, red dominance, darkness, and edge density.
   - For richer deployments, consider CLIP or SigLIP only when model size, latency, and cold start are acceptable.
   - Keep visual output in the same emotion schema as text.

4. Check semantic alignment.
   - Compare text and image valence, arousal, and primary emotions.
   - Label the relation as `aligned`, `contrast`, `weak`, or `unavailable`.
   - Surface contrast explicitly; in anime games, contrast can be a useful signal rather than an error, such as cheerful art paired with angry monetization feedback.

5. Fuse signals.
   - Weight each modality by confidence and task relevance.
   - Prefer explainable fusion over opaque averaging.
   - Include a trace that explains why the primary emotion, valence, arousal, and confidence changed.

## Output Pattern

Return:

- Primary emotion and emotion vector.
- Valence, arousal, and confidence.
- Evidence from each modality.
- Semantic alignment label and explanation when multimodal input exists.
- How the signal should affect the next agent step.

## Guardrails

- Do not infer protected attributes from player content.
- Do not treat one image mood score as proof of player intent.
- Escalate low-confidence or high-impact cases to human review rather than forcing a decisive label.
