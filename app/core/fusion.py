from __future__ import annotations

from app.core.schemas import EmotionVector, FusionResult, ImageSignal, TextSignal


EMOTION_FIELDS = tuple(EmotionVector.model_fields)


def fuse_signals(text: TextSignal | None, image: ImageSignal | None) -> FusionResult:
    if text is None and image is None:
        text = TextSignal(
            vector=EmotionVector(neutral=1.0),
            valence=0.0,
            arousal=0.05,
            confidence=0.1,
            evidence=["未提供输入，返回中性状态"],
            detected_terms=[],
        )

    weights = _weights(text, image)
    vector_values = {}
    for emotion in EMOTION_FIELDS:
        text_value = getattr(text.vector, emotion) if text else 0.0
        image_value = getattr(image.vector, emotion) if image else 0.0
        vector_values[emotion] = text_value * weights["text"] + image_value * weights["image"]

    vector_values = _normalize(vector_values)
    primary = max(vector_values, key=vector_values.get)
    valence = (text.valence * weights["text"] if text else 0.0) + (image.valence * weights["image"] if image else 0.0)
    arousal = (text.arousal * weights["text"] if text else 0.0) + (image.arousal * weights["image"] if image else 0.0)
    confidence = (text.confidence * weights["text"] if text else 0.0) + (
        image.confidence * weights["image"] if image else 0.0
    )

    explanation = [
        f"融合权重：文本 {weights['text']:.2f}，图像 {weights['image']:.2f}",
        f"主情绪：{primary}，效价 {valence:.2f}，唤醒度 {arousal:.2f}",
    ]
    if text and image:
        if abs(text.valence - image.valence) > 0.55:
            explanation.append("文本与图像效价差异较大，提示玩家语义和画面氛围存在反差")
        if text.confidence < 0.35 and image.confidence > 0.5:
            explanation.append("文本证据较弱，图像氛围对判断贡献更高")

    return FusionResult(
        vector=EmotionVector(**vector_values),
        primary_emotion=primary,
        valence=round(max(-1.0, min(1.0, valence)), 3),
        arousal=round(max(0.0, min(1.0, arousal)), 3),
        confidence=round(max(0.0, min(1.0, confidence)), 3),
        explanation=explanation,
    )


def _weights(text: TextSignal | None, image: ImageSignal | None) -> dict[str, float]:
    if text and not image:
        return {"text": 1.0, "image": 0.0}
    if image and not text:
        return {"text": 0.0, "image": 1.0}
    assert text is not None and image is not None
    text_weight = 0.62 * max(text.confidence, 0.15)
    image_weight = 0.38 * max(image.confidence, 0.15)
    total = text_weight + image_weight
    return {"text": text_weight / total, "image": image_weight / total}


def _normalize(values: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, value) for value in values.values())
    if total <= 0:
        return {key: 1.0 if key == "neutral" else 0.0 for key in values}
    return {key: round(max(0.0, value) / total, 3) for key, value in values.items()}

