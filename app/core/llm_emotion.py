from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from app.core.config import get_settings
from app.core.schemas import EmotionVector, TextSignal


MODEL_EMOTION_CN = {
    "joy": "喜悦",
    "sadness": "失落",
    "anger": "愤怒",
    "fear": "焦虑",
    "trust": "信任",
    "surprise": "惊讶",
    "anticipation": "期待",
    "disgust": "反感",
    "neutral": "中性",
}


def classify_text_with_deepseek(text: str) -> TextSignal | None:
    settings = get_settings()
    if not settings.deepseek_api_key or not text.strip():
        return None

    prompt = (
        "你是二次元手游玩家反馈情绪分类器。只返回 JSON，不要解释。"
        "字段：emotion(joy/sadness/anger/fear/trust/surprise/anticipation/disgust/neutral), "
        "valence(-1到1), arousal(0到1), confidence(0到1), evidence(中文短句数组)。\n"
        f"玩家反馈：{text[:1000]}"
    )
    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": "Return compact valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 240,
    }
    request = urllib.request.Request(
        url=settings.deepseek_base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.deepseek_api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
    parsed = _parse_json_object(content)
    if not parsed:
        return None

    emotion = parsed.get("emotion", "neutral")
    if emotion not in EmotionVector.model_fields:
        emotion = "neutral"

    vector = {key: 0.0 for key in EmotionVector.model_fields}
    vector[emotion] = 1.0
    confidence = _clip(parsed.get("confidence", 0.62), 0.0, 1.0)
    evidence = parsed.get("evidence") if isinstance(parsed.get("evidence"), list) else []
    evidence = [str(item)[:80] for item in evidence[:4]]
    evidence.insert(0, f"DeepSeek 分类为{MODEL_EMOTION_CN.get(emotion, emotion)}")

    return TextSignal(
        vector=EmotionVector(**vector),
        valence=round(_clip(parsed.get("valence", 0.0), -1.0, 1.0), 3),
        arousal=round(_clip(parsed.get("arousal", 0.35), 0.0, 1.0), 3),
        confidence=round(confidence, 3),
        evidence=evidence,
        detected_terms=[f"model:{emotion}"],
    )


def blend_text_signals(lexicon: TextSignal, model: TextSignal | None) -> TextSignal:
    if model is None:
        return lexicon

    model_weight = min(0.72, max(0.35, model.confidence))
    lexicon_weight = 1.0 - model_weight
    vector = {}
    for key in EmotionVector.model_fields:
        vector[key] = round(getattr(lexicon.vector, key) * lexicon_weight + getattr(model.vector, key) * model_weight, 3)

    return TextSignal(
        vector=EmotionVector(**vector),
        valence=round(lexicon.valence * lexicon_weight + model.valence * model_weight, 3),
        arousal=round(lexicon.arousal * lexicon_weight + model.arousal * model_weight, 3),
        confidence=round(max(lexicon.confidence, model.confidence), 3),
        evidence=[*model.evidence, *lexicon.evidence[:3], "中文模型与词典 baseline 融合输出"],
        detected_terms=[*lexicon.detected_terms, *model.detected_terms],
    )


def _parse_json_object(content: str) -> dict | None:
    try:
        value = json.loads(content)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            return None
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, dict) else None


def _clip(value: object, low: float, high: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = low
    return min(high, max(low, number))
