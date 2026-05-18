from __future__ import annotations

import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Lock

from app.core.agent import build_agent_advice
from app.core.config import get_settings
from app.core.fusion import fuse_signals
from app.core.schemas import BatchAnalyzeRequest, JobStatus
from app.core.text_emotion import analyze_text
from app.core.video_emotion import analyze_video


_executor = ThreadPoolExecutor(max_workers=get_settings().async_worker_count)
_jobs: dict[str, JobStatus] = {}
_cache: dict[str, dict] = {}
_lock = Lock()


def submit_batch_analysis(request: BatchAnalyzeRequest) -> JobStatus:
    cache_key = _hash("|".join(request.samples) + request.archetype)
    return _submit("batch-analysis", cache_key, lambda: _run_batch(request))


def submit_video_analysis(payload: bytes, filename: str, max_frames: int) -> JobStatus:
    cache_key = _hash(payload.hex()[:4096] + filename + str(max_frames))
    return _submit("video-analysis", cache_key, lambda: analyze_video(payload, filename, max_frames).model_dump())


def get_job(job_id: str) -> JobStatus | None:
    return _jobs.get(job_id)


def _submit(kind: str, cache_key: str, runner) -> JobStatus:
    now = _now()
    if cache_key in _cache:
        job = JobStatus(
            job_id=f"cached-{cache_key[:12]}",
            kind=kind,
            status="finished",
            created_at=now,
            updated_at=now,
            cache_key=cache_key,
            result=_cache[cache_key],
        )
        _jobs[job.job_id] = job
        return job

    job = JobStatus(
        job_id=str(uuid.uuid4()),
        kind=kind,
        status="queued",
        created_at=now,
        updated_at=now,
        cache_key=cache_key,
    )
    with _lock:
        _jobs[job.job_id] = job
    _executor.submit(_execute, job.job_id, runner)
    return job


def _execute(job_id: str, runner) -> None:
    _update(job_id, status="running")
    try:
        result = runner()
    except Exception as exc:
        _update(job_id, status="failed", error=str(exc))
        return

    cache_key = _jobs[job_id].cache_key
    if cache_key:
        _cache[cache_key] = result
    _update(job_id, status="finished", result=result)


def _run_batch(request: BatchAnalyzeRequest) -> dict:
    items = []
    for index, text in enumerate(request.samples):
        text_signal = analyze_text(text)
        fusion = fuse_signals(text_signal, None)
        advice = build_agent_advice(text_signal, None, fusion, request.archetype)
        items.append(
            {
                "index": index,
                "text": text,
                "primary_emotion": fusion.primary_emotion,
                "risk_level": advice.risk_level,
                "reply": advice.player_reply,
            }
        )
    return {"total": len(items), "items": items}


def _update(job_id: str, **changes) -> None:
    with _lock:
        job = _jobs[job_id]
        payload = job.model_dump()
        payload.update(changes)
        payload["updated_at"] = _now()
        _jobs[job_id] = JobStatus(**payload)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(UTC).isoformat()
