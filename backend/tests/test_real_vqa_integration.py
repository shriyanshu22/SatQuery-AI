from __future__ import annotations

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from backend.core.config import Settings
from backend.core.types import RSDataObject, RSMetadata, Modality
from backend.api.schemas import QueryRequest
from backend.api.orchestrator import QueryOrchestrator
from backend.models.mock_vlm import MockVLM


@pytest.fixture
def mock_rs_data():
    """Create a dummy RSDataObject for testing."""
    metadata = RSMetadata(
        crs="EPSG:4326",
        transform=None,
        bounds=(0.0, 0.0, 1.0, 1.0),
        resolution=(10.0, 10.0),
        band_count=3,
        band_names=["R", "G", "B"],
        dtype="uint8",
        nodata=None,
        width=100,
        height=100,
        file_format="geotiff",
        acquisition_date="2026-09-16T00:00:00Z",
        modality=Modality.OPTICAL,
    )
    return RSDataObject(
        data=np.zeros((3, 100, 100), dtype=np.uint8),
        metadata=metadata,
        source_path="/tmp/fake.tif",
        image_id="test_image_123"
    )


def test_orchestrator_mock_backend(mock_rs_data):
    """Test that MOCK backend correctly selects MockVLM."""
    settings = Settings()
    settings.model.backend_type = "MOCK"
    
    orchestrator = QueryOrchestrator(settings)
    request = QueryRequest(query="What is this?", image_ids=["test_image_123"])
    
    result = orchestrator.execute(request, mock_rs_data)
    
    # Must use MockVLM
    assert result.metadata["model"] == "mock-vlm"
    assert result.metadata["backend_type"] == "MOCK"
    assert result.answer.startswith("This is a deterministic answer to:")
    assert result.confidence.value == 0.99
    
    # Check trace
    actions = [step.action for step in result.execution_trace]
    assert "input_validated" in actions
    assert "vqa_tool_selected" in actions
    assert "inference_executed" in actions


@pytest.mark.skipif(
    not patch("backend.models.qwen_vlm.HAS_TRANSFORMERS", True), 
    reason="Only run if testing real integration environment"
)
def test_orchestrator_real_backend_selection(mock_rs_data):
    """Test that REAL backend correctly attempts to select QwenVLM."""
    settings = Settings()
    settings.model.backend_type = "REAL"
    
    orchestrator = QueryOrchestrator(settings)
    request = QueryRequest(query="What is this?", image_ids=["test_image_123"])
    
    # Mock the singleton getter to avoid actually loading the 3B model in regular tests
    with patch("backend.api.orchestrator._get_real_vlm") as mock_get_vlm:
        # Give it a mocked QwenVLM
        mock_vlm = MagicMock()
        mock_vlm.is_loaded.return_value = True
        
        info = MagicMock()
        info.name = "Qwen/Qwen2.5-VL-3B-Instruct"
        info.backend_type = "transformers_int4"
        mock_vlm.get_model_info.return_value = info
        
        from backend.core.protocols import VLMResult
        from backend.core.confidence import ConfidenceScore
        mock_result = VLMResult(
            answer="Real model mocked answer",
            evidence=[],
            confidence=ConfidenceScore.unavailable("test"),
            raw_output={"inference_duration_ms": 10.5}
        )
        mock_vlm.predict.return_value = mock_result
        
        mock_get_vlm.return_value = mock_vlm
        
        result = orchestrator.execute(request, mock_rs_data)
        
        mock_get_vlm.assert_called_once()
        mock_vlm.predict.assert_called_once()
        
        assert result.metadata["model"] == "Qwen/Qwen2.5-VL-3B-Instruct"
        assert result.answer == "Real model mocked answer"
        assert isinstance(result.metadata["inference_duration_ms"], float)
        assert result.metadata["inference_duration_ms"] >= 0.0
