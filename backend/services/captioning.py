from __future__ import annotations

from backend.core.types import RSDataObject, AnalysisResult, QueryIntent
from backend.core.evidence import MetadataEvidence
from backend.core.confidence import ConfidenceScore
from backend.core.protocols import VLMProtocol
from backend.preprocessing.adapters import ModelAdapter
from backend.core.logging import get_logger

logger = get_logger(__name__)


class CaptioningService:
    """Optional service for generating descriptive image captions."""
    
    def __init__(self, model: VLMProtocol, adapter: ModelAdapter):
        self.model = model
        self.adapter = adapter

    def caption_image(self, image: RSDataObject) -> AnalysisResult:
        """
        Generate a descriptive text caption for the remote sensing image.
        """
        logger.info(f"Generating caption for image {image.image_id}")
        
        adapted_data = self.adapter.adapt(image)
        # Using VLM with a default captioning prompt
        prompt = "Provide a detailed caption for this remote sensing image, describing key geographical features, land cover, and any prominent structures."
        result = self.model.predict(adapted_data, prompt)
        
        evidence = [
            MetadataEvidence(
                source_file=image.image_id,
                crs=image.metadata.crs,
                resolution=image.metadata.resolution,
                bounds=image.metadata.bounds,
                band_count=image.metadata.band_count,
                acquisition_date=image.metadata.acquisition_date
            )
        ]
        
        conf_val = result.confidence.value if result.confidence else 1.0
        confidence = ConfidenceScore(
            value=conf_val,
            source="vlm_model" if conf_val is not None else "unavailable",
            method="Caption generation confidence."
        )
        
        return AnalysisResult(
            answer=result.answer,
            confidence=confidence,
            evidence=evidence,
            execution_trace=[],
            metadata={"service": "CaptioningService"},
            warnings=[],
            errors=[],
            intent=QueryIntent.CAPTIONING
        )
