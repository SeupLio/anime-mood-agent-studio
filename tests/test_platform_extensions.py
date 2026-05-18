from __future__ import annotations

import time

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_model_status_exposes_expanded_backends() -> None:
    response = client.get("/api/model-status")
    payload = response.json()

    assert response.status_code == 200
    assert payload["rag_backend"] == "embedding-rerank"
    assert payload["rag_embedding_backend"] == "hashing"
    assert payload["chinese_emotion_model_id"]


def test_drift_report_compares_versions() -> None:
    response = client.get("/api/drift?baseline_version=3.0&current_version=5.7")
    payload = response.json()

    assert response.status_code == 200
    assert payload["baseline_version"] == "3.0"
    assert payload["current_version"] == "5.7"
    assert payload["segments"]
    assert payload["segments"][0]["metrics"]


def test_batch_analysis_job_finishes_and_caches() -> None:
    response = client.post(
        "/api/batch/jobs",
        json={"samples": ["这次活动太离谱了，我要退坑了！", "新角色好看，剧情也很期待。"], "archetype": "冷静策士"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] in {"queued", "running", "finished"}

    job = _wait_for_job(payload["job_id"])
    assert job["status"] == "finished"
    assert job["result"]["total"] == 2
    assert job["result"]["items"][0]["risk_level"] == "high"


def test_reply_experiment_creates_variants_and_review_gate() -> None:
    response = client.post(
        "/api/reply-experiment",
        data={"text": "这次礼包说明太离谱了，感觉有点骗氪。", "archetype": "冷静策士"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert len(payload["variants"]) == 3
    assert payload["review"]["status"] == "pending"
    assert payload["metrics"]["manual_review_required"] == 1.0


def test_hard_examples_endpoint_is_backed_by_evaluation() -> None:
    eval_response = client.get("/api/evaluation?limit=24")
    hard_response = client.get("/api/evaluation/hard-examples")

    assert eval_response.status_code == 200
    assert hard_response.status_code == 200
    assert isinstance(hard_response.json()["items"], list)


def _wait_for_job(job_id: str) -> dict:
    for _ in range(20):
        response = client.get(f"/api/jobs/{job_id}")
        payload = response.json()
        if payload["status"] in {"finished", "failed"}:
            return payload
        time.sleep(0.05)
    raise AssertionError("job did not finish")
