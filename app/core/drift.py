from __future__ import annotations

import math
from collections import Counter

from app.core.feedback_store import NEGATIVE_EMOTIONS, load_feedback_rows
from app.core.schemas import DriftMetric, DriftReport, DriftSegment


HIGH_RISK = {"高", "严重", "high", "critical"}


def detect_version_drift(
    baseline_version: str | None = None,
    current_version: str | None = None,
    event_name: str | None = None,
) -> DriftReport:
    rows = load_feedback_rows()
    versions = sorted({row.get("version", "") for row in rows if row.get("version")})
    baseline_version = baseline_version or (versions[0] if versions else "")
    current_version = current_version or (versions[-1] if versions else "")
    baseline = _filter(rows, baseline_version, event_name)
    current = _filter(rows, current_version, event_name)

    metrics = _drift_metrics(baseline, current)
    segments = [
        DriftSegment(
            version=current_version,
            event_name=event_name or "ALL",
            sample_size=len(current),
            metrics=metrics,
        )
    ]
    severity = _overall(metrics)
    return DriftReport(
        baseline_version=baseline_version,
        current_version=current_version,
        event_name=event_name,
        baseline_size=len(baseline),
        current_size=len(current),
        overall_severity=severity,
        segments=segments,
        recommendations=_recommendations(severity, metrics),
    )


def _filter(rows: list[dict[str, str]], version: str, event_name: str | None) -> list[dict[str, str]]:
    filtered = [row for row in rows if row.get("version") == version]
    if event_name:
        filtered = [row for row in filtered if row.get("event_name") == event_name]
    return filtered


def _drift_metrics(baseline: list[dict[str, str]], current: list[dict[str, str]]) -> list[DriftMetric]:
    return [
        _rate_metric("negative_rate", baseline, current, lambda row: row.get("fused_emotion") in NEGATIVE_EMOTIONS),
        _rate_metric("high_risk_rate", baseline, current, lambda row: row.get("risk_level") in HIGH_RISK),
        _distribution_metric("emotion_js_divergence", baseline, current, "fused_emotion"),
        _distribution_metric("intent_js_divergence", baseline, current, "intent"),
    ]


def _rate_metric(name: str, baseline: list[dict[str, str]], current: list[dict[str, str]], predicate) -> DriftMetric:
    base = sum(1 for row in baseline if predicate(row)) / max(len(baseline), 1)
    now = sum(1 for row in current if predicate(row)) / max(len(current), 1)
    delta = now - base
    return DriftMetric(
        name=name,
        baseline_value=round(base, 3),
        current_value=round(now, 3),
        delta=round(delta, 3),
        severity=_severity(abs(delta), watch=0.08, alert=0.16),
    )


def _distribution_metric(name: str, baseline: list[dict[str, str]], current: list[dict[str, str]], field: str) -> DriftMetric:
    base_dist = _distribution(row.get(field, "") for row in baseline)
    current_dist = _distribution(row.get(field, "") for row in current)
    value = _jensen_shannon(base_dist, current_dist)
    return DriftMetric(
        name=name,
        baseline_value=0.0,
        current_value=round(value, 3),
        delta=round(value, 3),
        severity=_severity(value, watch=0.12, alert=0.24),
    )


def _distribution(values) -> dict[str, float]:
    counter = Counter(value or "unknown" for value in values)
    total = sum(counter.values()) or 1
    return {key: count / total for key, count in counter.items()}


def _jensen_shannon(left: dict[str, float], right: dict[str, float]) -> float:
    keys = set(left) | set(right)
    middle = {key: (left.get(key, 0.0) + right.get(key, 0.0)) / 2 for key in keys}
    return math.sqrt((_kl(left, middle, keys) + _kl(right, middle, keys)) / 2)


def _kl(left: dict[str, float], right: dict[str, float], keys: set[str]) -> float:
    total = 0.0
    for key in keys:
        value = left.get(key, 0.0)
        if value > 0:
            total += value * math.log(value / max(right.get(key, 1e-9), 1e-9), 2)
    return total


def _severity(value: float, watch: float, alert: float) -> str:
    if value >= alert:
        return "alert"
    if value >= watch:
        return "watch"
    return "stable"


def _overall(metrics: list[DriftMetric]) -> str:
    if any(metric.severity == "alert" for metric in metrics):
        return "alert"
    if any(metric.severity == "watch" for metric in metrics):
        return "watch"
    return "stable"


def _recommendations(severity: str, metrics: list[DriftMetric]) -> list[str]:
    hot = [metric.name for metric in metrics if metric.severity != "stable"]
    if severity == "stable":
        return ["当前版本情绪分布与 baseline 接近，继续按日监控即可。"]
    actions = ["按版本、活动和渠道拆分复核 drift 来源，优先查看高风险样本。"]
    if "high_risk_rate" in hot:
        actions.append("高风险比例漂移明显，建议触发客服主管人工复核和公告口径检查。")
    if "emotion_js_divergence" in hot:
        actions.append("情绪分布漂移明显，建议把新增样本加入持续评估集。")
    return actions
