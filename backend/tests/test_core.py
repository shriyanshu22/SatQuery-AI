"""Core module tests."""

from __future__ import annotations

import pytest

from backend.core.evidence import (
    BoundingBox,
    BoundingBoxEvidence,
    ChangeMapEvidence,
    ChangedRegion,
    CrossModalAgreementEvidence,
    NumericalEvidence,
    serialize_evidence,
)
from backend.core.confidence import ConfidenceScore
from backend.core.types import (
    RSDataObject,
    RSMetadata,
    QueryIntent,
    ExecutionStep,
    AnalysisResult,
)
from backend.core.exceptions import (
    SatQueryError,
    ValidationError,
    ModelTimeoutError,
    ModelInferenceError,
)


class TestEvidence:
    """Tests for typed evidence dataclasses."""

    def test_bounding_box_evidence_creation(self) -> None:
        """BoundingBoxEvidence wraps a list of BoundingBox objects."""
        box = BoundingBox(x=0, y=0, w=10, h=10, label="building", confidence=0.9)
        evidence = BoundingBoxEvidence(
            boxes=[box],
            source_image_id="img_01",
            model_source="mock_vlm",
        )
        assert evidence.type == "bounding_box"
        assert len(evidence.boxes) == 1
        assert evidence.boxes[0].label == "building"
        assert evidence.boxes[0].confidence == 0.9

    def test_change_map_evidence_creation(self) -> None:
        """ChangeMapEvidence stores change detection results."""
        region = ChangedRegion(
            centroid=(5.0, 5.0),
            area=100.0,
            bbox=BoundingBox(x=0, y=0, w=10, h=10, label="change", confidence=1.0)
        )
        evidence = ChangeMapEvidence(
            source="test_model",
            confidence=0.8,
            mask_data=None, # mock
            regions=[region]
        )
        assert evidence.type == "change_map"
        assert len(evidence.regions) == 1

    def test_cross_modal_agreement_creation(self) -> None:
        """CrossModalAgreementEvidence records optical/SAR agreement."""
        evidence = CrossModalAgreementEvidence(
            source="cross_modal",
            confidence=0.9,
            agreement_level="agree",
            supporting_optical=[],
            supporting_sar=[],
            conflict_details="Both modalities detected the same building footprint."
        )
        assert evidence.type == "cross_modal_agreement"
        assert evidence.agreement_level == "agree"

    def test_serialize_evidence(self) -> None:
        """serialize_evidence returns a JSON-safe dict."""
        box = BoundingBox(x=1, y=2, w=3, h=4, label="road", confidence=0.8)
        evidence = BoundingBoxEvidence(
            boxes=[box],
            source_image_id="img_02",
            model_source="grounding_dino",
        )
        result = serialize_evidence(evidence)
        assert isinstance(result, dict)
        assert result["type"] == "bounding_box"
        assert result["source_image_id"] == "img_02"

    def test_numerical_evidence(self) -> None:
        """NumericalEvidence stores a computed metric."""
        evidence = NumericalEvidence(
            metric_name="NDVI_mean",
            value=0.72,
            unit=None,
            description="Mean NDVI across the ROI.",
        )
        assert evidence.type == "numerical"
        assert evidence.value == 0.72
        assert evidence.metric_name == "NDVI_mean"


class TestConfidence:
    """Tests for typed confidence scoring."""

    def test_unavailable_confidence(self) -> None:
        """ConfidenceScore.unavailable() sets value=None and source='unavailable'."""
        conf = ConfidenceScore.unavailable("Model did not return confidence")
        assert conf.value is None
        assert conf.source == "unavailable"
        assert conf.calibrated is False

    def test_model_logits_confidence(self) -> None:
        """ConfidenceScore.from_model_logits() stores raw model probability."""
        conf = ConfidenceScore.from_model_logits(0.85, method="Softmax max probability")
        assert conf.value == 0.85
        assert conf.source == "model_logits"

    def test_evidence_agreement_confidence(self) -> None:
        """ConfidenceScore.from_evidence_agreement() records cross-source score."""
        conf = ConfidenceScore.from_evidence_agreement(0.78, method="Optical-SAR IoU overlap")
        assert conf.value == 0.78
        assert conf.source == "evidence_agreement"

    def test_confidence_to_dict(self) -> None:
        """to_dict() returns all four fields."""
        conf = ConfidenceScore.from_model_logits(0.92, method="argmax")
        d = conf.to_dict()
        assert set(d.keys()) == {"value", "source", "method", "calibrated"}
        assert d["value"] == 0.92

    def test_confidence_value_none_when_unavailable(self) -> None:
        """When unavailable, value must be None — never fabricated."""
        conf = ConfidenceScore.unavailable("No logits available")
        assert conf.value is None
        assert "No logits" in conf.method


class TestTypes:
    """Tests for shared type definitions."""

    def test_rs_data_object_creation(self, sample_rs_data_object) -> None:
        """RSDataObject binds pixel data with metadata and an ID."""
        assert sample_rs_data_object.image_id == "test_img_01"
        assert sample_rs_data_object.data is not None
        assert sample_rs_data_object.data.shape == (3, 256, 256)

    def test_rs_metadata_creation(self, sample_rs_metadata) -> None:
        """RSMetadata contains CRS, resolution, and band info."""
        assert sample_rs_metadata.crs == "EPSG:32633"
        assert sample_rs_metadata.band_count == 3

    def test_query_intent_enum(self) -> None:
        """QueryIntent covers all expected analysis modes."""
        assert QueryIntent.VQA.value == "VQA"
        assert QueryIntent.CHANGE_DETECTION.value == "CHANGE_DETECTION"
        assert QueryIntent.UNKNOWN.value == "UNKNOWN"
        # Verify all expected members exist
        expected = {"VQA", "GROUNDING", "CHANGE_DETECTION", "SAR_ANALYSIS", "CROSS_MODAL", "CAPTIONING", "UNKNOWN"}
        assert set(QueryIntent.__members__.keys()) == expected

    def test_execution_step_creation(self) -> None:
        """ExecutionStep captures a single observable action."""
        step = ExecutionStep(
            step_number=1,
            action="route_query",
            status="completed",
            duration_ms=100.0,
            observable_output="Routed to VQA pipeline",
        )
        assert step.action == "route_query"
        assert step.status == "completed"


class TestExceptions:
    """Tests for the exception hierarchy."""

    def test_satquery_error_hierarchy(self) -> None:
        """All custom exceptions inherit from SatQueryError."""
        err = ValidationError("Invalid file format")
        assert isinstance(err, SatQueryError)
        assert isinstance(err, Exception)

    def test_validation_error_details(self) -> None:
        """SatQueryError stores structured details dict."""
        err = ValidationError(
            "Bad format",
            details={"field": "image", "reason": "unsupported extension"},
        )
        assert err.details["field"] == "image"
        assert err.message == "Bad format"

    def test_model_timeout_error(self) -> None:
        """ModelTimeoutError preserves original exception reference."""
        original = TimeoutError("Connection timed out")
        err = ModelTimeoutError(
            "Inference exceeded 60s",
            original_exception=original,
        )
        assert isinstance(err, SatQueryError)
        assert err.original_exception is original

