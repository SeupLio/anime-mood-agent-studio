from __future__ import annotations

import io
import math

from PIL import Image

from app.core.config import get_settings
from app.core.schemas import ImageSignal, SemanticSignal, TextSignal


EMOTION_PROMPTS = {
    "joy": "bright joyful anime game art",
    "sadness": "melancholy sad anime game art",
    "anger": "intense angry battle scene",
    "fear": "tense fearful dangerous scene",
    "trust": "calm reliable comforting scene",
    "surprise": "dramatic surprising scene",
    "anticipation": "hopeful exciting upcoming event",
    "disgust": "unpleasant frustrating scene",
    "neutral": "neutral game screenshot",
}


def analyze_semantic_alignment(
    text: str,
    image_bytes: bytes | None,
    text_signal: TextSignal | None,
    image_signal: ImageSignal | None,
) -> SemanticSignal | None:
    if not text.strip() or image_bytes is None or text_signal is None or image_signal is None:
        return None

    settings = get_settings()
    backend = settings.multimodal_backend.lower()
    if backend in {"clip", "siglip"}:
        model_result = _try_clip_or_siglip(text, image_bytes, backend)
        if model_result is not None:
            return model_result

    return _fallback_semantic(text_signal, image_signal, backend)


def _try_clip_or_siglip(text: str, image_bytes: bytes, backend: str) -> SemanticSignal | None:
    try:
        import torch
        from transformers import AutoModel, AutoProcessor
    except ImportError:
        return None

    settings = get_settings()
    model_id = settings.multimodal_model_id
    try:
        processor = AutoProcessor.from_pretrained(model_id, cache_dir=str(settings.cache_dir))
        model = AutoModel.from_pretrained(model_id, cache_dir=str(settings.cache_dir))
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        labels = list(EMOTION_PROMPTS.values())
        inputs = processor(text=[text, *labels], images=image, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
    except Exception:
        return None

    logits = getattr(outputs, "logits_per_image", None)
    if logits is None:
        return None

    scores = logits[0].softmax(dim=0).tolist()
    text_score = float(scores[0])
    best_prompt_score = max(float(item) for item in scores[1:])
    consistency = _clip(0.35 + text_score * 1.4 + best_prompt_score * 0.3, 0.0, 1.0)
    contrast = 1.0 - consistency
    label = "aligned" if consistency >= 0.62 else "contrast" if contrast >= 0.52 else "weak"
    return SemanticSignal(
        backend=f"{backend}:{model_id}",
        consistency_score=round(consistency, 3),
        contrast_score=round(contrast, 3),
        label=label,
        evidence=[
            f"{backend.upper()} 图文相似度参与判断",
            "若部署环境未缓存模型，可切换 MULTIMODAL_BACKEND=fallback",
        ],
    )


def _fallback_semantic(text_signal: TextSignal, image_signal: ImageSignal, requested_backend: str) -> SemanticSignal:
    text_primary = _primary(text_signal.vector.model_dump())
    image_primary = _primary(image_signal.vector.model_dump())
    valence_gap = abs(text_signal.valence - image_signal.valence)
    arousal_gap = abs(text_signal.arousal - image_signal.arousal)
    primary_bonus = 0.22 if text_primary == image_primary else 0.0
    consistency = _clip(1.0 - valence_gap * 0.75 - arousal_gap * 0.25 + primary_bonus, 0.0, 1.0)
    contrast = _clip(valence_gap * 0.72 + (0.18 if text_primary != image_primary else 0.0), 0.0, 1.0)
    if contrast >= 0.52:
        label = "contrast"
    elif consistency >= 0.62:
        label = "aligned"
    else:
        label = "weak"

    evidence = [
        f"文本主情绪 {text_primary}，图像主情绪 {image_primary}",
        f"效价差 {valence_gap:.2f}，唤醒度差 {arousal_gap:.2f}",
    ]
    if requested_backend in {"clip", "siglip"}:
        evidence.append("CLIP/SigLIP 依赖或模型不可用，使用可解释 fallback")

    return SemanticSignal(
        backend="fallback-semantic",
        consistency_score=round(consistency, 3),
        contrast_score=round(contrast, 3),
        label=label,
        evidence=evidence,
    )


def _primary(values: dict[str, float]) -> str:
    return max(values, key=values.get)


def _clip(value: float, low: float, high: float) -> float:
    if math.isnan(value):
        return low
    return max(low, min(high, value))
