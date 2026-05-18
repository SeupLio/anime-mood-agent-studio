from __future__ import annotations

import hashlib

from app.core.agent import build_agent_advice
from app.core.fusion import fuse_signals
from app.core.schemas import ReplyExperiment, ReplyVariant, ReviewQueueItem
from app.core.text_emotion import analyze_text


def build_reply_experiment(text: str, archetype: str = "温柔治愈") -> ReplyExperiment:
    signal = analyze_text(text)
    fusion = fuse_signals(signal, None)
    advice = build_agent_advice(signal, None, fusion, archetype)
    experiment_id = _id("exp", text + archetype)
    variants = _variants(advice.player_reply, advice.risk_level)
    best = max(variants, key=lambda item: item.score)
    review = None
    if advice.risk_level in {"medium", "high"}:
        review = ReviewQueueItem(
            review_id=_id("review", experiment_id),
            risk_level=advice.risk_level,
            reason="中高风险客服回复进入人工复核流，避免自动口径扩大舆情。",
            status="pending",
            selected_variant_id=best.variant_id,
        )
    return ReplyExperiment(
        experiment_id=experiment_id,
        text=text,
        intent=advice.intent,
        risk_level=advice.risk_level,
        variants=variants,
        review=review,
        metrics={
            "expected_resolution_rate": round(sum(item.score for item in variants) / max(len(variants), 1), 3),
            "manual_review_required": 1.0 if review else 0.0,
            "high_risk_guardrail": 1.0 if advice.risk_level == "high" else 0.0,
        },
    )


def _variants(base_reply: str, risk_level: str) -> list[ReplyVariant]:
    empathy = f"{base_reply} 我们会把你的体验作为优先反馈记录，并在有进展时同步说明。"
    action = f"{base_reply} 当前会先核对版本、区服、时间点和相关活动配置，再决定补偿或公告动作。"
    concise = base_reply
    risk_penalty = 0.08 if risk_level == "high" else 0.0
    return [
        ReplyVariant(
            variant_id="A",
            strategy="empathy_first",
            player_reply=empathy,
            expected_metric="negative_sentiment_reduction",
            score=round(0.72 - risk_penalty, 3),
        ),
        ReplyVariant(
            variant_id="B",
            strategy="action_first",
            player_reply=action,
            expected_metric="ticket_resolution_rate",
            score=round(0.78 if risk_level != "low" else 0.68, 3),
        ),
        ReplyVariant(
            variant_id="C",
            strategy="concise_control",
            player_reply=concise,
            expected_metric="reply_acceptance_rate",
            score=0.62,
        ),
    ]


def _id(prefix: str, seed: str) -> str:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{digest}"
