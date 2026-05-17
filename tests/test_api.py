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


def test_cors_allows_static_page_api_calls() -> None:
    response = client.options(
        "/api/analyze",
        headers={
            "Origin": "null",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


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
    assert payload["semantic"] is not None
    assert payload["fusion"]["confidence"] > 0.2
    assert payload["agent"]["ops_actions"]


def test_dashboard_uses_imported_feedback_dataset() -> None:
    response = client.get("/api/dashboard")
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] >= 200
    assert payload["clusters"]
    assert payload["risk_samples"]


def test_rag_returns_citations() -> None:
    response = client.post("/api/rag", data={"question": "维护延迟补偿怎么回复玩家？"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["citations"]
    assert "补偿" in payload["answer"]


def test_video_timeline_accepts_gif_upload() -> None:
    frames = [
        Image.new("RGB", (64, 64), (250, 230, 160)),
        Image.new("RGB", (64, 64), (40, 52, 120)),
        Image.new("RGB", (64, 64), (220, 40, 32)),
    ]
    buffer = io.BytesIO()
    frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:], duration=80, loop=0)
    buffer.seek(0)

    response = client.post(
        "/api/video",
        data={"max_frames": "3"},
        files={"video": ("sample.gif", buffer, "image/gif")},
    )
    payload = response.json()

    assert response.status_code == 200
    assert len(payload["frames"]) == 3
    assert payload["summary"]
