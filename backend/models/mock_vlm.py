"""Mock model implementations for deterministic testing.

These mock models satisfy the VLMProtocol and GroundingProtocol and return 
fully deterministic outputs for unit testing and demo mode.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from backend.core.confidence import ConfidenceScore
from backend.core.evidence import BoundingBox, NumericalEvidence
from backend.core.protocols import (
    GroundingProtocol,
    GroundingResult,
    ModelInfo,
    VLMProtocol,
    VLMResult,
)
from backend.models.base import BaseModel, ModelRegistry

logger = logging.getLogger(__name__)


class MockVLM(BaseModel, VLMProtocol):
    """Deterministic Mock VLM for testing VQA."""

    def __init__(self, name: str = "mock-vlm") -> None:
        super().__init__(name)

    def load(self) -> None:
        logger.info(f"Loading MockVLM {self.name}")
        self._loaded = True

    def unload(self) -> None:
        logger.info(f"Unloading MockVLM {self.name}")
        self._loaded = False

    def predict(self, image: np.ndarray, prompt: str, **kwargs: Any) -> VLMResult:
        if not self.is_loaded():
            raise RuntimeError(f"Model {self.name} is not loaded.")

        logger.debug(f"MockVLM processing prompt: '{prompt}' on image shape {image.shape}")

        answer = f"This is a deterministic answer to: '{prompt}'"
        
        # Mock models emit some basic numerical evidence to show they processed something
        evidence = [
            NumericalEvidence(
                metric_name="mock_activation_level",
                value=0.95,
                unit=None,
                description="Deterministic mock activation metric."
            )
        ]
        
        confidence = ConfidenceScore.from_model_logits(0.99, "Mock deterministic logits")

        return VLMResult(
            answer=answer,
            evidence=evidence,
            confidence=confidence,
            raw_output={"prompt": prompt, "status": "mocked"}
        )

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            name=self.name,
            version="1.0.0-mock",
            backend_type="MOCK",
            description="A strictly deterministic mock VLM for tests."
        )


class MockGroundingModel(BaseModel, GroundingProtocol):
    """Deterministic Mock Grounding model for testing."""

    def __init__(self, name: str = "mock-grounding") -> None:
        super().__init__(name)

    def load(self) -> None:
        logger.info(f"Loading MockGroundingModel {self.name}")
        self._loaded = True

    def unload(self) -> None:
        logger.info(f"Unloading MockGroundingModel {self.name}")
        self._loaded = False

    def ground(self, image: np.ndarray, text_query: str, **kwargs: Any) -> GroundingResult:
        if not self.is_loaded():
            raise RuntimeError(f"Model {self.name} is not loaded.")

        logger.debug(f"MockGroundingModel processing query: '{text_query}' on image shape {image.shape}")

        height, width = image.shape[-2:]

        # Create a deterministic bounding box in the center of the image
        cx, cy = width / 2.0, height / 2.0
        w, h = width * 0.1, height * 0.1
        
        mock_box = BoundingBox(
            x=cx,
            y=cy,
            w=w,
            h=h,
            label=text_query,
            confidence=0.88
        )

        confidence = ConfidenceScore.from_model_logits(0.88, "Mock box confidence")

        return GroundingResult(
            boxes=[mock_box],
            evidence=[], # The service wraps the boxes into BoundingBoxEvidence
            confidence=confidence,
            raw_output={"query": text_query, "status": "mocked"}
        )

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            name=self.name,
            version="1.0.0-mock",
            backend_type="MOCK",
            description="A strictly deterministic mock Grounding model for tests."
        )


# Register models
registry = ModelRegistry()
registry.register("mock_vqa", VLMProtocol, MockVLM)
registry.register("mock_grounding", GroundingProtocol, MockGroundingModel)
