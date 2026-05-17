from __future__ import annotations

from collections import Counter

from app.core.config import get_settings
from app.core.feedback_store import load_feedback_rows
from app.core.schemas import ConfusionCell, EvaluationExample, EvaluationMetric, EvaluationReport
from app.core.text_emotion import analyze_text


NEGATIVE = {"sadness", "anger", "fear", "disgust"}


def evaluate_text_emotion(limit: int = 240) -> EvaluationReport:
    rows = [row for row in load_feedback_rows() if row.get("text") and row.get("text_emotion")]
    rows = rows[: max(1, min(limit, len(rows)))]
    acceptable_labels = _acceptable_labels(rows)

    expected: list[str] = []
    predicted: list[str] = []
    confidence: list[float] = []
    compatible_hits = 0
    hard_examples: list[EvaluationExample] = []

    for row in rows:
        signal = analyze_text(row["text"])
        pred = _primary(signal.vector.model_dump())
        gold = row["text_emotion"]
        labels = acceptable_labels[row["text"]]
        expected.append(gold)
        predicted.append(pred)
        confidence.append(signal.confidence)
        if pred in labels:
            compatible_hits += 1
        if pred not in labels and len(hard_examples) < 12:
            hard_examples.append(
                EvaluationExample(
                    feedback_id=row.get("feedback_id", ""),
                    text=row["text"],
                    expected="/".join(sorted(labels)),
                    predicted=pred,
                    confidence=signal.confidence,
                    risk_level=row.get("risk_level", ""),
                )
            )

    return EvaluationReport(
        dataset_size=len(rows),
        backend=get_settings().text_emotion_backend,
        metrics=_metrics(expected, predicted, confidence, compatible_hits, acceptable_labels),
        emotion_support=dict(Counter(expected)),
        confusion=_confusion(expected, predicted),
        hard_examples=hard_examples,
        recommendations=_recommendations(expected, predicted, hard_examples),
    )


def _primary(values: dict[str, float]) -> str:
    return max(values, key=values.get)


def _acceptable_labels(rows: list[dict[str, str]]) -> dict[str, set[str]]:
    labels: dict[str, set[str]] = {}
    for row in rows:
        labels.setdefault(row["text"], set()).add(row["text_emotion"])
    return labels


def _metrics(
    expected: list[str],
    predicted: list[str],
    confidence: list[float],
    compatible_hits: int,
    acceptable_labels: dict[str, set[str]],
) -> list[EvaluationMetric]:
    total = len(expected)
    accuracy = sum(1 for gold, pred in zip(expected, predicted) if gold == pred) / max(total, 1)
    compatible_accuracy = compatible_hits / max(total, 1)
    macro_f1 = _macro_f1(expected, predicted)
    neg_recall = _negative_recall(expected, predicted)
    avg_conf = sum(confidence) / max(len(confidence), 1)
    conflict_rate = sum(1 for labels in acceptable_labels.values() if len(labels) > 1) / max(len(acceptable_labels), 1)
    return [
        EvaluationMetric(name="exact_accuracy", value=round(accuracy, 3), support=total),
        EvaluationMetric(name="compatible_accuracy", value=round(compatible_accuracy, 3), support=total),
        EvaluationMetric(name="macro_f1", value=round(macro_f1, 3), support=total),
        EvaluationMetric(name="negative_recall", value=round(neg_recall, 3), support=sum(1 for item in expected if item in NEGATIVE)),
        EvaluationMetric(name="avg_confidence", value=round(avg_conf, 3), support=total),
        EvaluationMetric(name="label_conflict_rate", value=round(conflict_rate, 3), support=len(acceptable_labels)),
    ]


def _macro_f1(expected: list[str], predicted: list[str]) -> float:
    labels = sorted(set(expected) | set(predicted))
    scores = []
    for label in labels:
        tp = sum(1 for gold, pred in zip(expected, predicted) if gold == label and pred == label)
        fp = sum(1 for gold, pred in zip(expected, predicted) if gold != label and pred == label)
        fn = sum(1 for gold, pred in zip(expected, predicted) if gold == label and pred != label)
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        scores.append(2 * precision * recall / max(precision + recall, 1e-9))
    return sum(scores) / max(len(scores), 1)


def _negative_recall(expected: list[str], predicted: list[str]) -> float:
    gold_negative = [index for index, item in enumerate(expected) if item in NEGATIVE]
    if not gold_negative:
        return 0.0
    hits = sum(1 for index in gold_negative if predicted[index] in NEGATIVE)
    return hits / len(gold_negative)


def _confusion(expected: list[str], predicted: list[str]) -> list[ConfusionCell]:
    pairs = Counter(zip(expected, predicted))
    return [
        ConfusionCell(expected=gold, predicted=pred, count=count)
        for (gold, pred), count in pairs.most_common(18)
    ]


def _recommendations(expected: list[str], predicted: list[str], hard_examples: list[EvaluationExample]) -> list[str]:
    confusion = Counter((gold, pred) for gold, pred in zip(expected, predicted) if gold != pred)
    recommendations = []
    for (gold, pred), count in confusion.most_common(3):
        recommendations.append(f"优先补强 {gold} 被误判为 {pred} 的样本，当前出现 {count} 次")
    if hard_examples:
        recommendations.append("将 hard examples 加入小规模人工标注集，用于回归测试和 prompt/词典迭代")
    recommendations.append("线上可按版本、活动和渠道分桶监控指标，避免总体准确率掩盖高风险场景退化")
    return recommendations[:4]
