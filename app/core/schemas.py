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
    fusion: FusionResult
    agent: AgentAdvice

