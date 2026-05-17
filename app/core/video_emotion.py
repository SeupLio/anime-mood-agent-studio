from __future__ import annotations

import io
import tempfile
from collections import Counter
from pathlib import Path

from PIL import Image, ImageSequence

from app.core.image_emotion import analyze_image
from app.core.schemas import VideoFrameSignal, VideoTimeline


def analyze_video(video_bytes: bytes, filename: str, max_frames: int = 8) -> VideoTimeline:
    frames = _extract_frames(video_bytes, filename, max_frames)
    if not frames:
        raise ValueError("未能从视频中抽取画面帧")

    frame_signals = []
    for index, frame in enumerate(frames):
        buffer = io.BytesIO()
        frame.convert("RGB").save(buffer, format="PNG")
        frame_signals.append(
            VideoFrameSignal(
                frame_index=index,
                timestamp_sec=round(index * 1.5, 2),
                image=analyze_image(buffer.getvalue()),
            )
        )

    emotions = [max(item.image.vector.model_dump(), key=item.image.vector.model_dump().get) for item in frame_signals]
    primary = Counter(emotions).most_common(1)[0][0]
    avg_valence = sum(item.image.valence for item in frame_signals) / len(frame_signals)
    avg_arousal = sum(item.image.arousal for item in frame_signals) / len(frame_signals)

    return VideoTimeline(
        filename=filename,
        frames=frame_signals,
        primary_emotion=primary,  # type: ignore[arg-type]
        avg_valence=round(avg_valence, 3),
        avg_arousal=round(avg_arousal, 3),
        summary=[
            f"抽取 {len(frame_signals)} 帧生成画面情绪时间线",
            f"主导画面情绪为 {primary}",
            "后续可接入 ASR 字幕和音频情绪，将台词/声线与画面同步融合",
        ],
    )


def _extract_frames(video_bytes: bytes, filename: str, max_frames: int) -> list[Image.Image]:
    suffix = Path(filename).suffix.lower()
    if suffix in {".gif", ".webp"}:
        return _extract_image_sequence(video_bytes, max_frames)
    return _extract_with_imageio(video_bytes, suffix or ".mp4", max_frames)


def _extract_image_sequence(video_bytes: bytes, max_frames: int) -> list[Image.Image]:
    with Image.open(io.BytesIO(video_bytes)) as image:
        frames = [frame.copy().convert("RGB") for frame in ImageSequence.Iterator(image)]
    return _sample(frames, max_frames)


def _extract_with_imageio(video_bytes: bytes, suffix: str, max_frames: int) -> list[Image.Image]:
    try:
        import imageio.v3 as iio
    except ImportError as exc:
        raise ValueError("视频抽帧需要安装 imageio[ffmpeg]，GIF/WebP 可直接分析") from exc

    with tempfile.NamedTemporaryFile(suffix=suffix) as handle:
        handle.write(video_bytes)
        handle.flush()
        raw_frames = []
        for index, frame in enumerate(iio.imiter(handle.name)):
            if index >= max_frames * 12:
                break
            if index % 12 == 0:
                raw_frames.append(Image.fromarray(frame).convert("RGB"))
        return _sample(raw_frames, max_frames)


def _sample(frames: list[Image.Image], max_frames: int) -> list[Image.Image]:
    if len(frames) <= max_frames:
        return frames
    step = max(1, len(frames) // max_frames)
    return frames[::step][:max_frames]
