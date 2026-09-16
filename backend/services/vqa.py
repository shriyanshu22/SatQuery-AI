"""Visual Question Answering (VQA) Service."""

from __future__ import annotations

import time
from typing import List

from backend.core.types import RSDataObject, AnalysisResult, ExecutionStep, QueryIntent
from backend.core.evidence import Evidence, MetadataEvidence
from backend.core.confidence import ConfidenceScore
from backend.core.protocols import VLMProtocol, VLMResult
from backend.preprocessing.adapters import ModelAdapter
from backend.core.logging import get_logger

logger = get_logger(__name__)


class VQAService:
    """Service handling Visual Question Answering over remote sensing data."""
    
    def __init__(self, model: VLMProtocol, adapter: ModelAdapter):
        self.model = model
        self.adapter = adapter

    def answer_question(self, image: RSDataObject, question: str) -> AnalysisResult:
        """Process an image and answer a question using the VLM.

        Args:
            image: The remote-sensing data object to analyse.
            question: Natural-language question from the user.

        Returns:
            Canonical AnalysisResult.
        """
        logger.info(f"Answering question '{question}' for image {image.image_id}")
        
        # 1. Adapt image for model
        adapted_data = self.adapter.adapt(image)
        
        # 2. Ensure model is loaded
        model_reused = self.model.is_loaded()
        if not model_reused:
            self.model.load()
            
        # 3. Run inference with timing
        t0 = time.perf_counter()
        result = self.model.predict(adapted_data, question)
        inference_ms = (time.perf_counter() - t0) * 1000.0
        
        # 4. Assemble evidence
        evidence_list = self._extract_evidence(image, result)
        
        # 5. Build metadata
        model_info = self.model.get_model_info()
        metadata = {
            "model": model_info.name,
            "backend_type": model_info.backend_type,
            "model_reused": model_reused,
            "inference_duration_ms": round(inference_ms, 2),
        }
        
        # 6. Trace
        trace = [
            ExecutionStep(
                step_number=1,
                action="input_validated",
                status="completed",
                duration_ms=None,
                observable_output=f"Image {image.image_id} adapted for VLM"
            ),
            ExecutionStep(
                step_number=2,
                action="vqa_tool_selected",
                status="completed",
                duration_ms=None,
                observable_output=f"Selected VQA with {model_info.name}"
            ),
            ExecutionStep(
                step_number=3,
                action="model_loaded" if not model_reused else "model_reused",
                status="completed",
                duration_ms=None,
                observable_output=f"{model_info.name} {'reused from memory' if model_reused else 'loaded fresh'}"
            ),
            ExecutionStep(
                step_number=4,
                action="inference_executed",
                status="completed",
                duration_ms=round(inference_ms, 2),
                observable_output="Generated answer"
            ),
        ]
        
        return AnalysisResult(
            answer=result.answer,
            confidence=result.confidence,
            evidence=evidence_list,
            execution_trace=trace,
            metadata=metadata,
            warnings=[],
            errors=[],
            intent=QueryIntent.VQA
        )

    def _extract_evidence(self, image: RSDataObject, result: VLMResult) -> List[Evidence]:
        """Combine image metadata evidence with model-emitted evidence."""
        evidence = list(result.evidence)
        
        # Add spatial metadata as evidence for context
        evidence.append(MetadataEvidence(
            source_file=image.image_id,
            crs=image.metadata.crs,
            resolution=image.metadata.resolution,
            bounds=image.metadata.bounds,
            band_count=image.metadata.band_count,
            acquisition_date=image.metadata.acquisition_date
        ))
            
        return evidence
