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
    hard_examples_path: Path = DATA_DIR / "hard_examples.jsonl"
    text_emotion_backend: str = os.getenv("TEXT_EMOTION_BACKEND", "lexicon")
    chinese_emotion_model_id: str = os.getenv(
        "CHINESE_EMOTION_MODEL_ID",
        "uer/roberta-base-finetuned-dianping-chinese",
    )
    multimodal_backend: str = os.getenv("MULTIMODAL_BACKEND", "fallback")
    multimodal_model_id: str = os.getenv("MULTIMODAL_MODEL_ID", "openai/clip-vit-base-patch32")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    enable_llm_rag: bool = os.getenv("ENABLE_LLM_RAG", "0") == "1"
    cache_dir: Path = Path(os.getenv("APP_CACHE_DIR", str(BASE_DIR / ".cache")))
    rag_backend: str = os.getenv("RAG_BACKEND", "embedding-rerank")
    rag_embedding_backend: str = os.getenv("RAG_EMBEDDING_BACKEND", "hashing")
    rag_reranker_backend: str = os.getenv("RAG_RERANKER_BACKEND", "lexical-cross")
    async_worker_count: int = int(os.getenv("ASYNC_WORKER_COUNT", "2"))


def get_settings() -> Settings:
    return Settings()
