from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


EmotionName = Literal[
    "joy",
    "sadness",
    "anger",
    "fear",
    "trust",
    "surprise",
    "anticipation",
    "disgust",
    "neutral",
]


class EmotionVector(BaseModel):
    joy: float = 0.0
    sadness: float = 0.0
    anger: float = 0.0
    fear: float = 0.0
    trust: float = 0.0
    surprise: float = 0.0
    anticipation: float = 0.0
    disgust: float = 0.0
    neutral: float = 0.0


class TextSignal(BaseModel):
    vector: EmotionVector
    valence: float = Field(ge=-1.0, le=1.0)
    arousal: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    detected_terms: list[str]


class ImageFeatures(BaseModel):
    brightness: float
    saturation: float
    contrast: float
    warmth: float
    coolness: float
    red_dominance: float
    darkness: float
    edge_density: float


class ImageSignal(BaseModel):
    vector: EmotionVector
    valence: float = Field(ge=-1.0, le=1.0)
    arousal: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    features: ImageFeatures
    evidence: list[str]


class FusionResult(BaseModel):
    vector: EmotionVector
    primary_emotion: EmotionName
    valence: float = Field(ge=-1.0, le=1.0)
    arousal: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: list[str]


class SemanticSignal(BaseModel):
    backend: str
    consistency_score: float = Field(ge=0.0, le=1.0)
    contrast_score: float = Field(ge=0.0, le=1.0)
    label: Literal["aligned", "contrast", "weak", "unavailable"]
    evidence: list[str]


class RagCitation(BaseModel):
    chunk_id: str
    source_doc: str
    title: str
    section: str
    score: float
    content: str
    tags: list[str] = []


class RagResponse(BaseModel):
    question: str
    answer: str
    citations: list[RagCitation]
    backend: str


class TrendPoint(BaseModel):
    date: str
    total: int
    negative: int
    high_risk: int
    avg_confidence: float


class FeedbackCluster(BaseModel):
    name: str
    size: int
    risk_level: str
    emotions: dict[str, int]
    top_terms: list[str]
    sample_ids: list[str]


class RiskSample(BaseModel):
    feedback_id: str
    created_at: str
    version: str
    event_name: str
    text: str
    fused_emotion: str
    risk_level: str
    recommended_action: str


class TrendDashboard(BaseModel):
    total: int
    filters: dict[str, str | None]
    risk_counts: dict[str, int]
    emotion_counts: dict[str, int]
    versions: list[str]
    events: list[str]
    trend: list[TrendPoint]
    clusters: list[FeedbackCluster]
    risk_samples: list[RiskSample]


class ConfusionCell(BaseModel):
    expected: str
    predicted: str
    count: int


class EvaluationMetric(BaseModel):
    name: str
    value: float
    support: int


class EvaluationExample(BaseModel):
    feedback_id: str
    text: str
    expected: str
    predicted: str
    confidence: float
    risk_level: str


class EvaluationReport(BaseModel):
    dataset_size: int
    backend: str
    metrics: list[EvaluationMetric]
    emotion_support: dict[str, int]
    confusion: list[ConfusionCell]
    hard_examples: list[EvaluationExample]
    recommendations: list[str]
    persisted_hard_examples: int = 0


class VideoFrameSignal(BaseModel):
    frame_index: int
    timestamp_sec: float
    image: ImageSignal


class VideoTimeline(BaseModel):
    filename: str
    frames: list[VideoFrameSignal]
    primary_emotion: EmotionName
    avg_valence: float
    avg_arousal: float
    summary: list[str]


class AgentStep(BaseModel):
    tool: str
    observation: str


class AgentAdvice(BaseModel):
    intent: str
    risk_level: Literal["low", "medium", "high"]
    response_strategy: str
    player_reply: str
    ops_actions: list[str]
    narrative_hook: str
    trace: list[AgentStep]


class AnalysisResponse(BaseModel):
    text: TextSignal | None
    image: ImageSignal | None
    semantic: SemanticSignal | None = None
    fusion: FusionResult
    agent: AgentAdvice


class DriftMetric(BaseModel):
    name: str
    baseline_value: float
    current_value: float
    delta: float
    severity: Literal["stable", "watch", "alert"]


class DriftSegment(BaseModel):
    version: str
    event_name: str
    sample_size: int
    metrics: list[DriftMetric]


class DriftReport(BaseModel):
    baseline_version: str
    current_version: str
    event_name: str | None = None
    baseline_size: int
    current_size: int
    overall_severity: Literal["stable", "watch", "alert"]
    segments: list[DriftSegment]
    recommendations: list[str]


class BatchAnalyzeRequest(BaseModel):
    samples: list[str] = Field(min_length=1, max_length=200)
    archetype: str = "温柔治愈"


class JobStatus(BaseModel):
    job_id: str
    kind: str
    status: Literal["queued", "running", "finished", "failed"]
    created_at: str
    updated_at: str
    cache_key: str | None = None
    result: dict | None = None
    error: str | None = None


class ReplyVariant(BaseModel):
    variant_id: str
    strategy: str
    player_reply: str
    expected_metric: str
    score: float


class ReviewQueueItem(BaseModel):
    review_id: str
    risk_level: str
    reason: str
    status: Literal["pending", "approved", "rejected"]
    selected_variant_id: str


class ReplyExperiment(BaseModel):
    experiment_id: str
    text: str
    intent: str
    risk_level: str
    variants: list[ReplyVariant]
    review: ReviewQueueItem | None = None
    metrics: dict[str, float]
