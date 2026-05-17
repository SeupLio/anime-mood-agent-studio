from __future__ import annotations

import colorsys
import io
import math

from PIL import Image, ImageStat

from app.core.schemas import EmotionVector, ImageFeatures, ImageSignal


def analyze_image(image_bytes: bytes) -> ImageSignal:
    with Image.open(io.BytesIO(image_bytes)) as raw:
        image = raw.convert("RGB")
        image.thumbnail((320, 320))
        pixels = list(image.get_flattened_data())

    brightness_values = [(r + g + b) / (3 * 255) for r, g, b in pixels]
    hsv = [colorsys.rgb_to_hsv(r / 255, g / 255, b / 255) for r, g, b in pixels]
    saturations = [item[1] for item in hsv]
    hues = [item[0] for item in hsv]

    brightness = _mean(brightness_values)
    saturation = _mean(saturations)
    contrast = min(1.0, ImageStat.Stat(image.convert("L")).stddev[0] / 80)
    warmth = _ratio(hues, lambda hue: hue <= 0.14 or hue >= 0.92)
    coolness = _ratio(hues, lambda hue: 0.52 <= hue <= 0.72)
    red_dominance = _ratio(pixels, lambda rgb: rgb[0] > rgb[1] * 1.25 and rgb[0] > rgb[2] * 1.25)
    darkness = _ratio(brightness_values, lambda value: value < 0.28)
    edge_density = _edge_density(image)

    scores = {
        "joy": max(0.0, brightness * 0.8 + saturation * 0.5 + warmth * 0.4 - darkness * 0.8),
        "sadness": max(0.0, darkness * 0.9 + coolness * 0.5 - saturation * 0.2),
        "anger": max(0.0, red_dominance * 1.3 + saturation * 0.25 + contrast * 0.2),
        "fear": max(0.0, darkness * 0.6 + contrast * 0.45 + coolness * 0.25),
        "trust": max(0.0, brightness * 0.45 + coolness * 0.25 - contrast * 0.15),
        "surprise": max(0.0, contrast * 0.55 + edge_density * 0.8 + saturation * 0.2),
        "anticipation": max(0.0, brightness * 0.35 + saturation * 0.35 + warmth * 0.2),
        "disgust": max(0.0, darkness * 0.35 + saturation * 0.15 - brightness * 0.1),
        "neutral": 0.15,
    }
    vector = _normalize(scores)
    valence = _valence(brightness, saturation, warmth, darkness, red_dominance)
    arousal = max(0.05, min(1.0, saturation * 0.35 + contrast * 0.35 + edge_density * 0.2 + red_dominance * 0.4))
    confidence = min(1.0, 0.25 + abs(valence) * 0.25 + arousal * 0.35 + max(scores.values()) * 0.1)

    evidence = _image_evidence(brightness, saturation, contrast, warmth, coolness, darkness, red_dominance)

    return ImageSignal(
        vector=EmotionVector(**vector),
        valence=round(valence, 3),
        arousal=round(arousal, 3),
        confidence=round(confidence, 3),
        features=ImageFeatures(
            brightness=round(brightness, 3),
            saturation=round(saturation, 3),
            contrast=round(contrast, 3),
            warmth=round(warmth, 3),
            coolness=round(coolness, 3),
            red_dominance=round(red_dominance, 3),
            darkness=round(darkness, 3),
            edge_density=round(edge_density, 3),
        ),
        evidence=evidence,
    )


def _mean(values: list[float]) -> float:
    return sum(values) / max(len(values), 1)


def _ratio(values, predicate) -> float:
    if not values:
        return 0.0
    return sum(1 for value in values if predicate(value)) / len(values)


def _edge_density(image: Image.Image) -> float:
    grayscale = image.convert("L").resize((96, 96))
    width, height = grayscale.size
    data = grayscale.load()
    diffs = []
    for y in range(height - 1):
        for x in range(width - 1):
            dx = abs(data[x, y] - data[x + 1, y])
            dy = abs(data[x, y] - data[x, y + 1])
            diffs.append((dx + dy) / 510)
    return min(1.0, math.sqrt(_mean(diffs)) * 1.4)


def _normalize(scores: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, value) for value in scores.values())
    if total <= 0:
        return {key: 1.0 if key == "neutral" else 0.0 for key in scores}
    return {key: round(max(0.0, value) / total, 3) for key, value in scores.items()}


def _valence(brightness: float, saturation: float, warmth: float, darkness: float, red_dominance: float) -> float:
    raw = brightness * 0.9 + saturation * 0.2 + warmth * 0.25 - darkness * 0.9 - red_dominance * 0.35 - 0.35
    return max(-1.0, min(1.0, raw))


def _image_evidence(
    brightness: float,
    saturation: float,
    contrast: float,
    warmth: float,
    coolness: float,
    darkness: float,
    red_dominance: float,
) -> list[str]:
    evidence: list[str] = []
    if brightness > 0.62:
        evidence.append("画面亮度较高，倾向积极情绪")
    if darkness > 0.35:
        evidence.append("暗部占比较高，提示压抑或紧张氛围")
    if saturation > 0.45:
        evidence.append("饱和度较高，提升情绪唤醒度")
    if contrast > 0.45:
        evidence.append("对比度较强，提示冲突或惊讶感")
    if warmth > coolness and warmth > 0.25:
        evidence.append("暖色占优，偏向热烈或愉悦")
    if coolness > warmth and coolness > 0.25:
        evidence.append("冷色占优，偏向冷静、忧伤或未知感")
    if red_dominance > 0.18:
        evidence.append("红色强占比，可能关联愤怒、危机或战斗场景")
    if not evidence:
        evidence.append("图像特征接近中性，低强度参与融合")
    return evidence
