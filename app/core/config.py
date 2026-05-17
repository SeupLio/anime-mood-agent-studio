from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


@dataclass(frozen=True)
class Settings:
    feedback_path: Path = DATA_DIR / "player_feedback_samples.csv"
    rag_path: Path = DATA_DIR / "rag_knowledge_chunks.jsonl"
    text_emotion_backend: str = os.getenv("TEXT_EMOTION_BACKEND", "lexicon")
    multimodal_backend: str = os.getenv("MULTIMODAL_BACKEND", "fallback")
    multimodal_model_id: str = os.getenv("MULTIMODAL_MODEL_ID", "openai/clip-vit-base-patch32")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    enable_llm_rag: bool = os.getenv("ENABLE_LLM_RAG", "0") == "1"
    cache_dir: Path = Path(os.getenv("APP_CACHE_DIR", str(BASE_DIR / ".cache")))


def get_settings() -> Settings:
    return Settings()
