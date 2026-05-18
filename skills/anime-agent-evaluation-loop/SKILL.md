---
name: anime-agent-evaluation-loop
description: Use when evaluating anime mobile game agents with labeled feedback, emotion metrics, risk recall, hard examples, confusion matrices, regression tests, and iterative improvement plans.
---

# Anime Agent Evaluation Loop

Use this skill to keep anime-game agent improvements measurable.

## Evaluation Targets

Evaluate the part that changed:

- Text emotion analyzer.
- Image or video mood analyzer.
- Multimodal fusion.
- Semantic alignment.
- Intent and LiveOps risk triage.
- RAG answer coverage and citation quality.
- Player reply quality and policy compliance.

## Workflow

1. Define success criteria.
   - Example: improve negative recall without lowering overall compatible accuracy.
   - Example: reduce unsupported RAG answers.
   - Example: preserve high-risk monetization escalation.

2. Build or select a test set.
   - Use version, event, emotion, intent, and channel metadata when available.
   - Include hard examples: negation, mixed sentiment, sarcasm, fandom slang, image-text contrast, policy gaps.

3. Measure.
   - Classification: accuracy, macro-F1, negative recall, confusion cells, support by label.
   - Agent triage: high-risk recall, false escalation rate, action correctness.
   - RAG: citation coverage, unsupported claim rate, answer usefulness.
   - Reply quality: empathy, specificity, policy safety, persona consistency.

4. Inspect failures.
   - Sort by confidence, risk, and user impact.
   - Fix the smallest responsible component.
   - Add regression tests before changing behavior when a bug is reproducible.

5. Report.
   - Include metric deltas, hard examples, known limitations, and next experiment.
   - Avoid claiming broad model quality from synthetic or narrow data.

## Output Pattern

Return:

- Evaluation scope.
- Dataset or sample source.
- Metrics.
- Top failure patterns.
- Recommended smallest next change.
- Verification command or test plan.

## Guardrails

- Do not optimize only for aggregate accuracy when high-risk recall matters.
- Do not hide label noise; mark compatible labels or ambiguous examples.
- Do not treat synthetic data as production evidence without stating the limitation.
