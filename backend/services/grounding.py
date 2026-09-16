"""Text-Guided Grounding Service."""

from __future__ import annotations

from typing import List

from backend.core.types import RSDataObject, AnalysisResult, ExecutionStep, QueryIntent
from backend.core.evidence import Evidence, MetadataEvidence, BoundingBoxEvidence
from backend.core.confidence import ConfidenceScore
from backend.core.protocols import GroundingProtocol, GroundingResult
from backend.preprocessing.adapters import ModelAdapter
from backend.core.logging import get_logger

logger = get_logger(__name__)


class GroundingService:
    """Service handling text-guided spatial grounding."""
    
    def __init__(self, model: GroundingProtocol, adapter: ModelAdapter):
        self.model = model
        self.adapter = adapter

    def ground_query(self, image: RSDataObject, text_query: str) -> AnalysisResult:
        """
        Locate objects or features in the image described by the text query.
        """
        logger.info(f"Grounding query '{text_query}' on image {image.image_id}")
        
        # 1. Adapt data
        adapted_data = self.adapter.adapt(image)
        
        # 2. Ensure loaded
        if not self.model.is_loaded():
            self.model.load()
            
        # 3. Predict
        result = self.model.ground(adapted_data, text_query)
        
        # 4. Assemble evidence
        evidence_list = self._extract_evidence(image, result)
        
        # 5. Trace
        trace = [
            ExecutionStep(
                step_number=1,
                action=f"Grounding inference with {self.model.get_model_info().name}",
                status="completed",
                duration_ms=None,
                observable_output=f"Detected {len(result.boxes)} bounding boxes"
            )
        ]
        
        return AnalysisResult(
            answer=f"Found {len(result.boxes)} regions matching '{text_query}'.",
            confidence=result.confidence,
            evidence=evidence_list,
            execution_trace=trace,
            metadata={"model": self.model.get_model_info().name},
            warnings=[],
            errors=[],
            intent=QueryIntent.GROUNDING
        )

    def _extract_evidence(self, image: RSDataObject, result: GroundingResult) -> List[Evidence]:
        """Convert grounding results into formal Evidence objects."""
        evidence = list(result.evidence)
        
        # Bounding boxes
        if result.boxes:
            evidence.append(BoundingBoxEvidence(
                boxes=result.boxes,
                source_image_id=image.image_id,
                model_source=self.model.get_model_info().name
            ))
            
        # Metadata
        evidence.append(MetadataEvidence(
            source_file=image.image_id,
            crs=image.metadata.crs,
            resolution=image.metadata.resolution,
            bounds=image.metadata.bounds,
            band_count=image.metadata.band_count,
            acquisition_date=image.metadata.acquisition_date
        ))
            
        return evidence

