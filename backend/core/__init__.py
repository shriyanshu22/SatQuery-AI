"""Core package for SatQuery AI.

Exports key types including Evidence, ConfidenceScore, RSDataObject, and SatQueryError.
"""

from __future__ import annotations

from backend.core.evidence import Evidence
from backend.core.confidence import ConfidenceScore
from backend.core.types import (
    RSDataObject,
    RSMetadata,
    Modality,
    ValidationStatus,
    QueryIntent,
    ModelBackend,
    ExecutionStep,
    AnalysisResult,
)
from backend.core.exceptions import SatQueryError
from backend.core.artifacts import Artifact, ArtifactType, ArtifactStore

__all__ = [
    "Evidence",
    "ConfidenceScore",
    "RSDataObject",
    "RSMetadata",
    "Modality",
    "ValidationStatus",
    "QueryIntent",
    "ModelBackend",
    "SatQueryError",
    "Artifact",
    "ArtifactType",
    "ArtifactStore",
    "ExecutionStep",
    "AnalysisResult",
]
