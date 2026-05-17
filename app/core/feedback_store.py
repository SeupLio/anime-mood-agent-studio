from __future__ import annotations

import csv
from collections import Counter, defaultdict
from functools import lru_cache

from app.core.config import get_settings
from app.core.schemas import FeedbackCluster, RiskSample, TrendDashboard, TrendPoint


NEGATIVE_EMOTIONS = {"sadness", "anger", "fear", "disgust"}
HIGH_RISK = {"高", "严重", "high", "critical"}


@lru_cache(maxsize=1)
def load_feedback_rows() -> list[dict[str, str]]:
    path = get_settings().feedback_path
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_dashboard(version: str | None = None, event_name: str | None = None) -> TrendDashboard:
    rows = _filter_rows(load_feedback_rows(), version, event_name)
    risk_counts = Counter(row.get("risk_level", "未知") for row in rows)
    emotion_counts = Counter(row.get("fused_emotion", "neutral") for row in rows)
    versions = sorted({row.get("version", "") for row in load_feedback_rows() if row.get("version")})
    events = sorted({row.get("event_name", "") for row in load_feedback_rows() if row.get("event_name")})

    return TrendDashboard(
        total=len(rows),
        filters={"version": version, "event_name": event_name},
        risk_counts=dict(risk_counts),
        emotion_counts=dict(emotion_counts),
        versions=versions,
        events=events,
        trend=_trend(rows),
        clusters=_clusters(rows),
        risk_samples=_risk_samples(rows),
    )


def examples_from_dataset(limit: int = 6) -> list[dict[str, str]]:
    rows = load_feedback_rows()
    if not rows:
        return []
    picks = []
    seen_intents = set()
    for row in rows:
        intent = row.get("intent", "")
        if intent in seen_intents:
            continue
        seen_intents.add(intent)
        picks.append(
            {
                "title": intent or row.get("feedback_id", "样例"),
                "text": row.get("text", ""),
                "archetype": "冷静策士" if row.get("risk_level") in HIGH_RISK else "温柔治愈",
            }
        )
        if len(picks) >= limit:
            break
    return picks


def _filter_rows(rows: list[dict[str, str]], version: str | None, event_name: str | None) -> list[dict[str, str]]:
    filtered = rows
    if version:
        filtered = [row for row in filtered if row.get("version") == version]
    if event_name:
        filtered = [row for row in filtered if row.get("event_name") == event_name]
    return filtered


def _trend(rows: list[dict[str, str]]) -> list[TrendPoint]:
    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        day = row.get("created_at", "")[:10] or "unknown"
        buckets[day].append(row)

    points = []
    for day, items in sorted(buckets.items()):
        confidence = [_float(item.get("fused_confidence")) for item in items]
        points.append(
            TrendPoint(
                date=day,
                total=len(items),
                negative=sum(1 for item in items if item.get("fused_emotion") in NEGATIVE_EMOTIONS),
                high_risk=sum(1 for item in items if item.get("risk_level") in HIGH_RISK),
                avg_confidence=round(sum(confidence) / max(len(confidence), 1), 3),
            )
        )
    return points


def _clusters(rows: list[dict[str, str]], limit: int = 6) -> list[FeedbackCluster]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = row.get("intent") or row.get("event_name") or "未分类"
        grouped[key].append(row)

    clusters = []
    for name, items in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)[:limit]:
        risk_counter = Counter(item.get("risk_level", "未知") for item in items)
        emotion_counter = Counter(item.get("fused_emotion", "neutral") for item in items)
        terms = Counter()
        for item in items:
            for tag in item.get("tags", "").split("；"):
                if tag:
                    terms[tag] += 1
            if item.get("event_name"):
                terms[item["event_name"]] += 1
        clusters.append(
            FeedbackCluster(
                name=name,
                size=len(items),
                risk_level=risk_counter.most_common(1)[0][0],
                emotions=dict(emotion_counter),
                top_terms=[term for term, _ in terms.most_common(5)],
                sample_ids=[item.get("feedback_id", "") for item in items[:5]],
            )
        )
    return clusters


def _risk_samples(rows: list[dict[str, str]], limit: int = 10) -> list[RiskSample]:
    priority = {"严重": 0, "高": 1, "中": 2, "低": 3}
    sorted_rows = sorted(rows, key=lambda row: (priority.get(row.get("risk_level", ""), 9), row.get("created_at", "")))
    samples = []
    for row in sorted_rows[:limit]:
        samples.append(
            RiskSample(
                feedback_id=row.get("feedback_id", ""),
                created_at=row.get("created_at", ""),
                version=row.get("version", ""),
                event_name=row.get("event_name", ""),
                text=row.get("text", ""),
                fused_emotion=row.get("fused_emotion", ""),
                risk_level=row.get("risk_level", ""),
                recommended_action=row.get("recommended_action", ""),
            )
        )
    return samples


def _float(value: str | None) -> float:
    try:
        return float(value or 0.0)
    except ValueError:
        return 0.0
