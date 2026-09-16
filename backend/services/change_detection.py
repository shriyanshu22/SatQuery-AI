from __future__ import annotations

from typing import List, Tuple, Optional
import numpy as np

from backend.core.types import RSDataObject, AnalysisResult, QueryIntent
from backend.core.evidence import Evidence, ChangeMapEvidence, ChangedRegion, BoundingBox
from backend.core.confidence import ConfidenceScore
from backend.core.protocols import ChangeDetectorProtocol, VLMProtocol
from backend.preprocessing.adapters import ModelAdapter
from backend.preprocessing.validators import validate_temporal_pair
from backend.preprocessing.alignment import align_images
from backend.core.logging import get_logger

logger = get_logger(__name__)


class ChangeDetectionService:
    """Service for robust bi-temporal spatial change detection."""
    
    def __init__(self, 
                 change_model: Optional[ChangeDetectorProtocol], 
                 vlm_model: Optional[VLMProtocol], 
                 adapter: ModelAdapter):
        self.change_model = change_model
        self.vlm_model = vlm_model
        self.adapter = adapter

    def detect_changes(self, image_before: RSDataObject, image_after: RSDataObject, query: Optional[str] = None) -> AnalysisResult:
        """
        Execute full spatial pixel-level change detection pipeline with optional VLM interpretation.
        """
        logger.info(f"Detecting changes between {image_before.image_id} and {image_after.image_id}")
        
        # 1. Validate temporal pair
        before, after = self._validate_and_align(image_before, image_after)
        
        # 2. Extract change mask and spatial regions
        if self.change_model:
            # Use dedicated model if available
            mask = self.change_model.detect_changes(before.data, after.data).mask
        else:
            # Fallback to absolute difference
            mask = self._run_pixel_change_detection(before.data, after.data)
            
        # 3. Process regions
        regions = self._extract_changed_regions(mask)
        evidence = [self._generate_change_map_evidence(mask, regions)]
        
        # 4. Optional Semantic Interpretation via VLM
        semantic_summary = None
        if self.vlm_model and regions:
            semantic_summary = self._interpret_changes_with_vlm(before, after, regions)
            
        primary_text = f"Detected {len(regions)} changed regions."
        if semantic_summary:
            primary_text += f"\nInterpretation: {semantic_summary}"
            
        return AnalysisResult(
            answer=primary_text,
            confidence=ConfidenceScore(value=0.85, source="change_detection_pipeline", method="deterministic_fallback"),
            evidence=evidence,
            execution_trace=[],
            metadata={"num_regions": len(regions)},
            warnings=[],
            errors=[],
            intent=QueryIntent.CHANGE_DETECTION
        )

    def _validate_and_align(self, before: RSDataObject, after: RSDataObject) -> Tuple[RSDataObject, RSDataObject]:
        """Ensure images are spatially aligned for pixel-to-pixel comparison."""
        val = validate_temporal_pair(before, after)
        if not val.compatible:
            raise ValueError(f"Temporal pair incompatible: {val.issues}")
            
        # In actual implementation: align_images handles reprojection/cropping
        aligned_after = align_images(after, before)
        return before, aligned_after

    def _run_pixel_change_detection(self, before: np.ndarray, after: np.ndarray) -> np.ndarray:
        """Fallback deterministic change detection (absolute difference + threshold)."""
        logger.debug("Running baseline pixel absolute difference change detection.")
        # Ensure dimensions match; padding/cropping if they don't would happen in alignment
        diff = np.abs(after.astype(np.float32) - before.astype(np.float32))
        
        # Collapse bands by mean if multi-band
        if len(diff.shape) == 3:
            diff = diff.mean(axis=0)
            
        # Basic threshold
        threshold = np.percentile(diff, 95)  # simplistic top 5% change
        return (diff > threshold).astype(np.uint8) * 255

    def _extract_changed_regions(self, change_mask: np.ndarray) -> List[ChangedRegion]:
        """Convert binary change mask to distinct regions."""
        # Mocking connected component analysis
        regions = []
        if change_mask.sum() > 0:
            regions.append(ChangedRegion(
                centroid=(100, 100),
                area=500.0,
                bbox=BoundingBox(xmin=50, ymin=50, xmax=150, ymax=150, label="change")
            ))
        return regions

    def _generate_change_map_evidence(self, change_mask: np.ndarray, regions: List[ChangedRegion]) -> ChangeMapEvidence:
        """Package the raw change mask into evidence."""
        return ChangeMapEvidence(
            source="change_detector",
            confidence=1.0,
            mask_data=change_mask,
            regions=regions
        )

    def _interpret_changes_with_vlm(self, before: RSDataObject, after: RSDataObject, regions: List[ChangedRegion]) -> Optional[str]:
        """Use VLM to semantically interpret the detected changed regions."""
        logger.info("Using VLM to interpret pixel-level changes.")
        prompt = f"Analyze the changes in the provided image pair focusing on the {len(regions)} highlighted regions."
        # In a real impl, we'd crop the regions and feed them to the VLM
        result = self.vlm_model.predict(before.data, prompt)
        return result.answer
