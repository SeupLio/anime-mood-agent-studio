from __future__ import annotations

import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_text_only() -> None:
    response = client.post(
        "/api/analyze",
        data={"text": "新角色真的很好看，但我担心抽不到。", "archetype": "温柔治愈"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["text"] is not None
    assert payload["image"] is None
    assert payload["agent"]["intent"] in {"uncertainty_or_anxiety", "positive_feedback"}
    assert payload["agent"]["player_reply"]


def test_analyze_with_image_upload() -> None:
    image = Image.new("RGB", (80, 80), (24, 60, 140))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    response = client.post(
        "/api/analyze",
        data={"text": "这个战斗场景有点紧张，但我很期待后续。", "archetype": "元气伙伴"},
        files={"image": ("scene.png", buffer, "image/png")},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["image"] is not None
    assert payload["fusion"]["confidence"] > 0.2
    assert payload["agent"]["ops_actions"]

