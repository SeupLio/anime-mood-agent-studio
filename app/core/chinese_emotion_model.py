from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import get_settings
from app.core.schemas import EmotionVector, TextSignal


POSITIVE_LABELS = {"positive", "pos", "label_1", "1", "好评", "正向"}
NEGATIVE_LABELS = {"negative", "neg", "label_0", "0", "差评", "负向"}


def classify_text_with_chinese_model(text: str) -> TextSignal | None:
    if not text.strip():
        return None

    classifier = _load_pipeline()
    if classifier is None:
        return None

    try:
        raw = classifier(text[:512], truncation=True)
    except Exception:
        return None

    item = raw[0] if isinstance(raw, list) and raw else raw
    if not isinstance(item, dict):
        return None

    label = str(item.get("label", "neutral")).lower()
    score = _clip(item.get("score", 0.55), 0.0, 1.0)
    emotion = _map_label_to_emotion(label, text)
    vector = {key: 0.0 for key in EmotionVector.model_fields}
    vector[emotion] = 1.0

    valence = 0.58 if emotion in {"joy", "trust"} else -0.58 if emotion in {"anger", "sadness", "disgust"} else 0.0
    arousal = 0.58 if emotion in {"anger", "fear", "surprise", "anticipation"} else 0.32
    return TextSignal(
        vector=EmotionVector(**vector),
        valence=round(valence, 3),
        arousal=round(arousal, 3),
        confidence=round(score, 3),
        evidence=[f"中文情绪模型 {get_settings().chinese_emotion_model_id} 输出 {label}"],
        detected_terms=[f"zh-model:{emotion}"],
    )


@lru_cache(maxsize=1)
def _load_pipeline() -> Any | None:
    settings = get_settings()
    try:
        from transformers import pipeline
    except Exception:
        return None

    try:
        return pipeline("text-classification", model=settings.chinese_emotion_model_id)
    except Exception:
        return None


def _map_label_to_emotion(label: str, text: str) -> str:
    if label in POSITIVE_LABELS or "positive" in label:
        return "joy" if any(term in text for term in ("开心", "喜欢", "惊喜", "期待", "好看")) else "trust"
    if label in NEGATIVE_LABELS or "negative" in label:
        if any(term in text for term in ("骗氪", "垃圾", "离谱", "退坑", "生气")):
            return "anger"
        if any(term in text for term in ("担心", "焦虑", "怕")):
            return "fear"
        if any(term in text for term in ("恶心", "反感", "烦")):
            return "disgust"
        return "sadness"
    return "neutral"


def _clip(value: object, low: float, high: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = low
    return min(high, max(low, number))
