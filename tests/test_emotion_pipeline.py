from __future__ import annotations

import io

from PIL import Image

from app.core.agent import build_agent_advice
from app.core.fusion import fuse_signals
from app.core.image_emotion import analyze_image
from app.core.semantic import analyze_semantic_alignment
from app.core.text_emotion import analyze_text


def test_monetization_complaint_becomes_high_risk() -> None:
    text = analyze_text("这次礼包说明太离谱了，感觉有点骗氪，再这样我要退坑了！")
    fusion = fuse_signals(text, None)
    advice = build_agent_advice(text, None, fusion, "冷静策士")

    assert fusion.primary_emotion == "anger"
    assert fusion.valence < -0.4
    assert advice.intent == "monetization_complaint"
    assert advice.risk_level == "high"
    assert len(advice.trace) >= 4


def test_negated_positive_term_flips_to_negative_signal() -> None:
    text = analyze_text("这次剧情我不开心，也有点失望")

    assert text.vector.sadness > text.vector.joy
    assert text.valence < 0


def test_red_high_saturation_image_contributes_anger() -> None:
    image = Image.new("RGB", (96, 96), (230, 24, 20))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    signal = analyze_image(buffer.getvalue())

    assert signal.features.red_dominance > 0.9
    assert signal.vector.anger == max(signal.vector.model_dump().values())
    assert signal.arousal > 0.4


def test_multimodal_fusion_keeps_both_modalities() -> None:
    text = analyze_text("主线最后一幕太惊艳了，完全没想到，已经等不及下一章！")
    image = Image.new("RGB", (64, 64), (246, 188, 74))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    image_signal = analyze_image(buffer.getvalue())
    fusion = fuse_signals(text, image_signal)

    assert fusion.confidence > 0.35
    assert fusion.primary_emotion in {"joy", "anticipation", "surprise"}
    assert "融合权重" in fusion.explanation[0]


def test_semantic_fallback_detects_valence_contrast() -> None:
    text = analyze_text("这次活动太糟糕了，真的有点失望")
    image = Image.new("RGB", (64, 64), (250, 226, 120))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    image_signal = analyze_image(buffer.getvalue())
    semantic = analyze_semantic_alignment("这次活动太糟糕了，真的有点失望", buffer.getvalue(), text, image_signal)

    assert semantic is not None
    assert semantic.backend == "fallback-semantic"
    assert semantic.contrast_score > 0.4
