from __future__ import annotations

import math
import re

from app.core.config import get_settings
from app.core.chinese_emotion_model import classify_text_with_chinese_model
from app.core.llm_emotion import blend_text_signals, classify_text_with_deepseek
from app.core.schemas import EmotionVector, TextSignal


LEXICON: dict[str, dict[str, float]] = {
    "joy": {
        "开心": 1.0,
        "快乐": 1.0,
        "喜欢": 0.9,
        "好看": 0.8,
        "惊艳": 0.9,
        "治愈": 0.8,
        "爽": 0.7,
        "爱了": 1.0,
        "happy": 1.0,
        "love": 0.9,
        "amazing": 0.9,
        "cute": 0.7,
    },
    "sadness": {
        "难过": 1.0,
        "失望": 0.9,
        "破防": 0.9,
        "心累": 0.8,
        "哭": 0.8,
        "遗憾": 0.7,
        "sad": 1.0,
        "disappointed": 0.9,
        "tired": 0.7,
    },
    "anger": {
        "生气": 1.0,
        "愤怒": 1.0,
        "气死": 1.0,
        "离谱": 0.8,
        "垃圾": 1.0,
        "骗氪": 1.0,
        "退坑": 0.9,
        "吵起来": 0.8,
        "背刺": 0.9,
        "心态爆炸": 0.9,
        "angry": 1.0,
        "trash": 1.0,
        "scam": 1.0,
    },
    "fear": {
        "害怕": 1.0,
        "担心": 0.8,
        "焦虑": 0.9,
        "紧张": 0.7,
        "怕": 0.7,
        "恐怖": 0.9,
        "worried": 0.8,
        "afraid": 1.0,
        "anxious": 0.9,
    },
    "trust": {
        "安心": 1.0,
        "可靠": 0.9,
        "相信": 0.9,
        "良心": 0.8,
        "稳定": 0.7,
        "trust": 1.0,
        "reliable": 0.9,
    },
    "surprise": {
        "震惊": 1.0,
        "意外": 0.8,
        "没想到": 0.9,
        "惊喜": 0.9,
        "wow": 0.9,
        "surprised": 1.0,
    },
    "anticipation": {
        "期待": 1.0,
        "希望": 0.7,
        "等不及": 0.9,
        "想抽": 0.8,
        "想玩": 0.8,
        "期待后续": 1.0,
        "excited": 0.9,
        "looking forward": 1.0,
    },
    "disgust": {
        "恶心": 1.0,
        "反感": 0.9,
        "厌烦": 0.8,
        "烦": 0.7,
        "模糊": 0.6,
        "伤信任": 0.9,
        "不满": 0.8,
        "disgusting": 1.0,
        "annoying": 0.8,
    },
}

NEGATIONS = ("不", "没", "无", "别", "不是", "never", "not", "no")
INTENSIFIERS = ("很", "太", "超", "真的", "特别", "非常", "极其", "巨", "爆", "very", "so", "extremely")
POSITIVE_EMOJIS = ("😊", "😍", "🥰", "❤", "👍", "✨")
NEGATIVE_EMOJIS = ("😡", "😭", "💢", "👎", "😰", "😞")


def analyze_text(text: str) -> TextSignal:
    lexicon_signal = _analyze_text_with_lexicon(text)
    backend = get_settings().text_emotion_backend.lower()
    if backend == "lexicon":
        return lexicon_signal

    model_signal = classify_text_with_deepseek(text)
    if backend == "deepseek":
        if model_signal is None:
            lexicon_signal.evidence.append("DeepSeek 不可用，回退到词典 baseline")
            return lexicon_signal
        return model_signal

    if backend in {"zh-model", "chinese-model", "transformers"}:
        chinese_signal = classify_text_with_chinese_model(text)
        if chinese_signal is None:
            lexicon_signal.evidence.append("中文情绪模型不可用，回退到词典 baseline")
            return lexicon_signal
        return blend_text_signals(lexicon_signal, chinese_signal)

    if backend == "hybrid":
        return blend_text_signals(lexicon_signal, model_signal or classify_text_with_chinese_model(text))

    lexicon_signal.evidence.append(f"未知文本模型后端 {backend}，回退到词典 baseline")
    return lexicon_signal


def _analyze_text_with_lexicon(text: str) -> TextSignal:
    normalized = text.strip().lower()
    scores = {emotion: 0.0 for emotion in EmotionVector.model_fields}
    detected_terms: list[str] = []
    evidence: list[str] = []

    for emotion, terms in LEXICON.items():
        for term, weight in terms.items():
            for match in re.finditer(re.escape(term.lower()), normalized):
                modifier = _local_modifier(normalized, match.start())
                if modifier < 0:
                    scores[_negated_emotion(emotion)] += weight * abs(modifier) * 0.8
                    detected_terms.append(f"否定:{term}")
                else:
                    scores[emotion] += weight * modifier
                    detected_terms.append(term)

    pos_emoji_hits = sum(normalized.count(emoji) for emoji in POSITIVE_EMOJIS)
    neg_emoji_hits = sum(normalized.count(emoji) for emoji in NEGATIVE_EMOJIS)
    scores["joy"] += pos_emoji_hits * 0.8
    scores["trust"] += pos_emoji_hits * 0.3
    scores["sadness"] += neg_emoji_hits * 0.5
    scores["anger"] += normalized.count("😡") * 0.8 + normalized.count("💢") * 0.6

    exclamations = normalized.count("!") + normalized.count("！")
    questions = normalized.count("?") + normalized.count("？")
    scores["surprise"] += min(exclamations, 4) * 0.12
    scores["fear"] += min(questions, 3) * 0.08

    if not any(scores.values()) and normalized:
        scores["neutral"] = 1.0
        evidence.append("未命中强情绪词，视为中性反馈")
    elif not normalized:
        scores["neutral"] = 1.0
        evidence.append("未提供文本，文本模态不参与融合")

    vector = _normalize(scores)
    valence = _valence(scores)
    arousal = _arousal(scores, exclamations, questions)
    confidence = min(1.0, 0.2 + math.log1p(sum(scores.values())) / 2.5)

    if detected_terms:
        evidence.append("命中情绪词：" + "、".join(detected_terms[:8]))
    if exclamations:
        evidence.append("感叹号提升唤醒度")
    if questions:
        evidence.append("疑问句提示不确定或焦虑")

    return TextSignal(
        vector=EmotionVector(**vector),
        valence=round(valence, 3),
        arousal=round(arousal, 3),
        confidence=round(confidence, 3),
        evidence=evidence,
        detected_terms=detected_terms,
    )


def _local_modifier(text: str, start: int) -> float:
    window = text[max(0, start - 8) : start]
    modifier = 1.0
    if any(word in window for word in INTENSIFIERS):
        modifier *= 1.35
    if any(word in window for word in NEGATIONS):
        modifier *= -0.65
    return modifier


def _negated_emotion(emotion: str) -> str:
    return {
        "joy": "sadness",
        "trust": "fear",
        "anticipation": "sadness",
        "sadness": "trust",
        "anger": "trust",
        "fear": "trust",
        "disgust": "trust",
        "surprise": "neutral",
    }.get(emotion, "neutral")


def _normalize(scores: dict[str, float]) -> dict[str, float]:
    clipped = {key: max(0.0, value) for key, value in scores.items()}
    total = sum(clipped.values())
    if total <= 0:
        clipped["neutral"] = 1.0
        total = 1.0
    return {key: round(value / total, 3) for key, value in clipped.items()}


def _valence(scores: dict[str, float]) -> float:
    positive = scores["joy"] + scores["trust"] + scores["anticipation"] * 0.5
    negative = scores["anger"] + scores["sadness"] + scores["fear"] + scores["disgust"]
    total = positive + negative + 1e-6
    return max(-1.0, min(1.0, (positive - negative) / total))


def _arousal(scores: dict[str, float], exclamations: int, questions: int) -> float:
    active = scores["anger"] + scores["fear"] + scores["surprise"] + scores["anticipation"]
    calm = scores["trust"] + scores["sadness"] * 0.3
    base = active / (active + calm + 1.0)
    punctuation_boost = min(0.25, exclamations * 0.05 + questions * 0.03)
    return max(0.05, min(1.0, base + punctuation_boost))
