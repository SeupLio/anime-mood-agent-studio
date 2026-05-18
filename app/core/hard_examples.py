from __future__ import annotations

import json
from datetime import UTC, datetime

from app.core.config import get_settings
from app.core.schemas import EvaluationExample


def load_persisted_hard_examples(limit: int = 200) -> list[dict]:
    path = get_settings().hard_examples_path
    if not path.exists():
        return []
    examples = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                examples.append(json.loads(line))
    return examples[-limit:]


def persist_hard_examples(examples: list[EvaluationExample]) -> int:
    if not examples:
        return len(load_persisted_hard_examples())

    path = get_settings().hard_examples_path
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {item.get("feedback_id") for item in load_persisted_hard_examples(limit=5000)}
    now = datetime.now(UTC).isoformat()
    appended = 0
    with path.open("a", encoding="utf-8") as handle:
        for example in examples:
            if example.feedback_id in existing:
                continue
            payload = example.model_dump()
            payload["captured_at"] = now
            payload["source"] = "evaluation"
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            appended += 1
    return len(existing) + appended
