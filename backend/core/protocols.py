"""Protocol definitions for model interfaces and result structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import numpy as np

from backend.core.confidence import ConfidenceScore
from backend.core.evidence import Evidence


@dataclass
class ModelInfo:
    """Metadata about a specific model implementation."""
    name: str
    version: str
    backend_type: str
    description: str
    device: str | None = None
    parameters: int | None = None


@dataclass
class VLMResult:
    """Result from a Vision-Language Model prediction."""
    answer: str
    evidence: list[Evidence]
    confidence: ConfidenceScore
    raw_output: Any


@dataclass
class GroundingResult:
    """Result from a text-guided visual grounding model."""
    boxes: list[Any]  # Target BoundingBoxes from core.evidence
    evidence: list[Evidence]
    confidence: ConfidenceScore
    raw_output: Any


@dataclass
class ChangeDetectionResult:
    """Result from a bi-temporal change detection model."""
    change_mask: np.ndarray
    percent_changed: float
    evidence: list[Evidence]
    confidence: ConfidenceScore
    raw_output: Any


@dataclass
class SARAnalysisResult:
    """Result from a SAR image analysis model."""
    analysis: str
    evidence: list[Evidence]
    confidence: ConfidenceScore
    raw_output: Any


@runtime_checkable
class VLMProtocol(Protocol):
    """Interface for Vision-Language Models."""
    
    def predict(self, image: np.ndarray, prompt: str, **kwargs: Any) -> VLMResult:
        """Run VLM inference on an image and prompt."""
        ...
        
    def get_model_info(self) -> ModelInfo:
        """Get metadata about this model."""
        ...
        
    def is_loaded(self) -> bool:
        """Check if the model is currently loaded in memory."""
        ...


@runtime_checkable
class GroundingProtocol(Protocol):
    """Interface for text-guided visual grounding models."""
    
    def ground(self, image: np.ndarray, text_query: str, **kwargs: Any) -> GroundingResult:
        """Locate objects matching the text query in the image."""
        ...
        
    def get_model_info(self) -> ModelInfo:
        """Get metadata about this model."""
        ...
        
    def is_loaded(self) -> bool:
        """Check if the model is currently loaded in memory."""
        ...


@runtime_checkable
class ChangeDetectorProtocol(Protocol):
    """Interface for bi-temporal change detection models."""
    
    def detect_changes(self, image_before: np.ndarray, image_after: np.ndarray, **kwargs: Any) -> ChangeDetectionResult:
        """Detect changes between two temporally distinct images."""
        ...
        
    def get_model_info(self) -> ModelInfo:
        """Get metadata about this model."""
        ...
        
    def is_loaded(self) -> bool:
        """Check if the model is currently loaded in memory."""
        ...


@runtime_checkable
class SARAnalyzerProtocol(Protocol):
    """Interface for SAR image analysis models."""
    
    def analyze(self, sar_image: np.ndarray, query: str | None = None, **kwargs: Any) -> SARAnalysisResult:
        """Analyze a Synthetic Aperture Radar (SAR) image."""
        ...
        
    def get_model_info(self) -> ModelInfo:
        """Get metadata about this model."""
        ...
        
    def is_loaded(self) -> bool:
        """Check if the model is currently loaded in memory."""
        ...
