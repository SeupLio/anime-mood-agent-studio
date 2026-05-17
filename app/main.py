from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import UnidentifiedImageError

from app.core.agent import ARCHETYPES, build_agent_advice
from app.core.config import get_settings
from app.core.feedback_store import build_dashboard, examples_from_dataset
from app.core.fusion import fuse_signals
from app.core.image_emotion import analyze_image
from app.core.rag import answer_question
from app.core.schemas import AnalysisResponse, RagResponse, TrendDashboard, VideoTimeline
from app.core.semantic import analyze_semantic_alignment
from app.core.text_emotion import analyze_text
from app.core.video_emotion import analyze_video


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Anime Mood Agent Studio",
    description="Multimodal emotion fusion and agent advice for anime game feedback.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "anime-mood-agent-studio"}


@app.get("/api/model-status")
def model_status() -> dict[str, str | bool]:
    settings = get_settings()
    return {
        "text_emotion_backend": settings.text_emotion_backend,
        "deepseek_configured": bool(settings.deepseek_api_key),
        "deepseek_model": settings.deepseek_model,
        "multimodal_backend": settings.multimodal_backend,
        "multimodal_model_id": settings.multimodal_model_id,
        "rag_backend": "keyword-rag",
        "llm_rag_enabled": settings.enable_llm_rag,
    }


@app.get("/api/archetypes")
def archetypes() -> dict[str, list[str]]:
    return {"items": list(ARCHETYPES)}


@app.get("/api/examples")
def examples() -> dict[str, list[dict[str, str]]]:
    dataset_examples = examples_from_dataset(limit=6)
    if dataset_examples:
        return {"items": dataset_examples}
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
    image_bytes: bytes | None = None

    if image and image.filename:
        image_bytes = await image.read()
        try:
            image_signal = analyze_image(image_bytes)
        except UnidentifiedImageError as exc:
            raise HTTPException(status_code=400, detail="上传文件不是可识别的图片") from exc

    fusion = fuse_signals(text_signal, image_signal)
    semantic = analyze_semantic_alignment(text, image_bytes, text_signal, image_signal)
    agent = build_agent_advice(text_signal, image_signal, fusion, archetype)
    return AnalysisResponse(text=text_signal, image=image_signal, semantic=semantic, fusion=fusion, agent=agent)


@app.get("/api/dashboard", response_model=TrendDashboard)
def dashboard(version: str | None = None, event_name: str | None = None) -> TrendDashboard:
    return build_dashboard(version=version, event_name=event_name)


@app.post("/api/rag", response_model=RagResponse)
def rag(question: str = Form(default="维护补偿和客服回复需要注意什么？")) -> RagResponse:
    return answer_question(question)


@app.post("/api/video", response_model=VideoTimeline)
async def video(video: UploadFile = File(...), max_frames: int = Form(default=8)) -> VideoTimeline:
    payload = await video.read()
    try:
        return analyze_video(payload, video.filename or "upload.mp4", max_frames=max(1, min(max_frames, 16)))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
