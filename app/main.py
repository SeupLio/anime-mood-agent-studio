from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import UnidentifiedImageError

from app.core.agent import ARCHETYPES, build_agent_advice
from app.core.fusion import fuse_signals
from app.core.image_emotion import analyze_image
from app.core.schemas import AnalysisResponse
from app.core.text_emotion import analyze_text


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Anime Mood Agent Studio",
    description="Multimodal emotion fusion and agent advice for anime game feedback.",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "anime-mood-agent-studio"}


@app.get("/api/archetypes")
def archetypes() -> dict[str, list[str]]:
    return {"items": list(ARCHETYPES)}


@app.get("/api/examples")
def examples() -> dict[str, list[dict[str, str]]]:
    return {
        "items": [
            {
                "title": "卡池焦虑",
                "text": "新角色真的很好看，但我有点担心抽不到，活动时间也太紧了。",
                "archetype": "温柔治愈",
            },
            {
                "title": "付费不满",
                "text": "这次礼包说明太离谱了，感觉有点骗氪，再这样我要退坑了！",
                "archetype": "冷静策士",
            },
            {
                "title": "剧情期待",
                "text": "主线最后一幕太惊艳了，完全没想到，已经等不及下一章！",
                "archetype": "元气伙伴",
            },
        ]
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(
    text: str = Form(default=""),
    archetype: str = Form(default="温柔治愈"),
    image: UploadFile | None = File(default=None),
) -> AnalysisResponse:
    text_signal = analyze_text(text) if text.strip() else None
    image_signal = None

    if image and image.filename:
        image_bytes = await image.read()
        try:
            image_signal = analyze_image(image_bytes)
        except UnidentifiedImageError as exc:
            raise HTTPException(status_code=400, detail="上传文件不是可识别的图片") from exc

    fusion = fuse_signals(text_signal, image_signal)
    agent = build_agent_advice(text_signal, image_signal, fusion, archetype)
    return AnalysisResponse(text=text_signal, image=image_signal, fusion=fusion, agent=agent)

