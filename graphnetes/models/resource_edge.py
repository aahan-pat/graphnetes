from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .confidence import Confidence
from .edge_relation import EdgeRelation


@dataclass
class ResourceEdge:
    source_id: str
    target_id: str
    relation: EdgeRelation
    confidence: Confidence = Confidence.EXTRACTED
    confidence_score: float = 1.0       # 0.0–1.0; EXTRACTED always 1.0
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.confidence == Confidence.EXTRACTED and self.confidence_score != 1.0:
            raise ValueError("EXTRACTED edges must have confidence_score=1.0")
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(f"confidence_score must be in [0.0, 1.0], got {self.confidence_score}")
