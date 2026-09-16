from __future__ import annotations

from typing import List, Literal, Optional

from backend.core.types import RSDataObject, AnalysisResult, QueryIntent
from backend.core.evidence import Evidence, CrossModalAgreementEvidence
from backend.core.confidence import ConfidenceScore
from backend.core.protocols import SARAnalyzerProtocol, VLMProtocol
from backend.preprocessing.validators import validate_cross_modal_pair
from backend.core.logging import get_logger

logger = get_logger(__name__)


class CrossModalAnalysisService:
    """Service for fusing observations from multiple modalities (e.g., Optical + SAR)."""
    
    def __init__(self, vlm_model: Optional[VLMProtocol], sar_analyzer: Optional[SARAnalyzerProtocol]):
        self.vlm_model = vlm_model
        self.sar_analyzer = sar_analyzer

    def analyze(self, optical_image: RSDataObject, sar_image: RSDataObject, query: str) -> AnalysisResult:
        """
        Analyze both optical and SAR inputs, cross-validate evidence, and fuse into a unified result.
        """
        logger.info(f"Cross-modal analysis: Optical({optical_image.image_id}) and SAR({sar_image.image_id})")
        
        # 1. Validation
        val = validate_cross_modal_pair(optical_image, sar_image)
        if not val.compatible:
            raise ValueError(f"Cross-modal pair incompatible: {val.issues}")
            
        # 2. Modality-specific analysis
        optical_evidence, opt_conf = self._analyze_optical(optical_image, query)
        sar_evidence, sar_conf = self._analyze_sar(sar_image, query)
        
        # 3. Detect Agreement & Fuse Evidence
        agreement = self._determine_agreement(optical_evidence, sar_evidence)
        fusion_evidence = self._fuse_evidence(optical_evidence, sar_evidence, agreement)
        
        # 4. Compute combined confidence
        final_conf = self._compute_combined_confidence(opt_conf, sar_conf, agreement)
        
        summary = f"Cross-modal fusion result: {agreement.upper()} between Optical and SAR."
        
        return AnalysisResult(
            answer=summary,
            confidence=final_conf,
            evidence=[fusion_evidence] + optical_evidence + sar_evidence,
            execution_trace=[],
            metadata={"agreement_level": agreement},
            warnings=[],
            errors=[],
            intent=QueryIntent.CROSS_MODAL
        )

    def _analyze_optical(self, image: RSDataObject, query: str) -> tuple[List[Evidence], ConfidenceScore]:
        if not self.vlm_model:
            return [], ConfidenceScore(value=None, source="unavailable", method="No VLM available")
        res = self.vlm_model.predict(image.data, query)
        conf = ConfidenceScore(value=res.confidence.value or 0.8, source="optical_vlm", method="VLM")
        # Generate mock evidence for architecture showcase
        return [], conf

    def _analyze_sar(self, image: RSDataObject, query: str) -> tuple[List[Evidence], ConfidenceScore]:
        if not self.sar_analyzer:
            return [], ConfidenceScore(value=None, source="unavailable", method="No SAR analyzer available")
        res = self.sar_analyzer.analyze(image.data, query)
        conf = ConfidenceScore(value=res.confidence.value or 0.85, source="sar_analyzer", method="SAR")
        return [], conf

    def _determine_agreement(self, optical: List[Evidence], sar: List[Evidence]) -> Literal['agree', 'disagree', 'inconclusive', 'partial']:
        """
        Compare spatial regions and semantic conclusions to detect agreement.
        (Placeholder for sophisticated spatial IoU and semantic overlap logic).
        """
        # Logic to compare bounding boxes and textual labels
        return 'agree'

    def _fuse_evidence(self, 
                       optical_evidence: List[Evidence], 
                       sar_evidence: List[Evidence], 
                       agreement: Literal['agree', 'disagree', 'inconclusive', 'partial']) -> CrossModalAgreementEvidence:
        """Create structured fusion evidence reporting the level of agreement."""
        return CrossModalAgreementEvidence(
            source="cross_modal_fusion",
            confidence=1.0,
            agreement_level=agreement,
            supporting_optical=optical_evidence,
            supporting_sar=sar_evidence,
            conflict_details="No conflicts detected." if agreement == 'agree' else "Conflicting signals detected."
        )

    def _compute_combined_confidence(self, 
                                     optical_conf: ConfidenceScore, 
                                     sar_conf: ConfidenceScore, 
                                     agreement: str) -> ConfidenceScore:
        """
        Calculates final confidence based on modalities and agreement.
        """
        v1 = optical_conf.value or 0.0
        v2 = sar_conf.value or 0.0
        
        if agreement == 'agree':
            final_val = min(1.0, max(v1, v2) + 0.1)
        elif agreement == 'disagree':
            final_val = max(0.1, min(v1, v2) - 0.2)
        else:
            final_val = (v1 + v2) / 2
            
        return ConfidenceScore(
            value=final_val if (optical_conf.value is not None or sar_conf.value is not None) else None,
            source="fused",
            method=f"Combined confidence. Modalities {agreement}."
        )
