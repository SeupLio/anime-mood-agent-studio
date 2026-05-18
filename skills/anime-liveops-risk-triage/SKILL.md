---
name: anime-liveops-risk-triage
description: Use when designing or operating anime mobile game agents that triage player feedback into LiveOps risk levels, intents, recommended actions, support replies, escalation queues, and community monitoring workflows.
---

# Anime LiveOps Risk Triage

Use this skill to convert player feedback and fused emotion signals into operational decisions.

## Risk Signals

High risk usually includes:

- Monetization anger: gacha fairness, paid packs, misleading probability, refund pressure.
- Exit intent: uninstall, quit, chargeback, boycott, public escalation.
- Community spread: many players repeating the same complaint, streamer or forum amplification.
- Safety or compliance concerns: harassment, self-harm language, minors, payment disputes.

Medium risk usually includes:

- Negative valence with moderate arousal.
- Anxiety about event windows, progression, compensation, or unclear rules.
- Repeated confusion around the same announcement or UI flow.

Low risk usually includes:

- Positive feedback.
- Neutral feature requests.
- Isolated confusion with clear support guidance.

## Workflow

1. Detect intent.
   - Common intents: `monetization_complaint`, `negative_feedback`, `content_expectation`, `uncertainty_or_anxiety`, `positive_feedback`, `bug_report`, `scene_mood_check`, `general_feedback`.

2. Combine intent with emotion.
   - Anger plus monetization terms should escalate faster than generic anger.
   - Fear or sadness may need reassurance and clarity rather than defensive language.
   - Anticipation can become operationally valuable if clustered around unreleased content.

3. Assign risk.
   - Use `high`, `medium`, or `low`.
   - Include the rule or evidence that drove the label.
   - If evidence conflicts, choose the safer review path and mark uncertainty.

4. Draft actions.
   - High risk: human review, version/event linkage, payment or gacha log check, public FAQ candidate.
   - Medium risk: clarify rules, add support macro, monitor trend.
   - Low risk: record insight, route to content or UX backlog if useful.

5. Draft player-facing response.
   - Acknowledge the emotion first.
   - Avoid arguing with player perception.
   - Give a concrete next step, required information, or expected follow-up channel.
   - Match the selected character or support archetype without overplaying persona.

## Output Pattern

Return:

- Intent.
- Risk level.
- Evidence.
- Player reply.
- Operations actions.
- Trace of decision steps.

## Guardrails

- Do not promise compensation, refunds, drop rates, or release dates unless authoritative policy is provided.
- Do not use cute persona language to soften serious monetization or safety issues.
- Keep public-response suggestions consistent with official announcements and support policy.
