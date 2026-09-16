"""Visual Question Answering (VQA) Service."""

from __future__ import annotations

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
        """
        Process an image and answer a question using the VLM.
        """
        logger.info(f"Answering question '{question}' for image {image.image_id}")
        
        # 1. Adapt image for model
        adapted_data = self.adapter.adapt(image)
        
        # 2. Ensure model is loaded
        if not self.model.is_loaded():
            self.model.load()
            
        # 3. Run inference
        result = self.model.predict(adapted_data, question)
        
        # 4. Assemble evidence
        evidence_list = self._extract_evidence(image, result)
        
        # 6. Trace
        trace = [
            ExecutionStep(
                step_number=1,
                action=f"VQA inference with {self.model.get_model_info().name}",
                status="completed",
                duration_ms=None,
                observable_output="Generated answer"
            )
        ]
        
        return AnalysisResult(
            answer=result.answer,
            confidence=result.confidence,
            evidence=evidence_list,
            execution_trace=trace,
            metadata={"model": self.model.get_model_info().name},
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

