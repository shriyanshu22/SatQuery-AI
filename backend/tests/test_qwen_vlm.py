from __future__ import annotations

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from backend.models.qwen_vlm import QwenVLM, HAS_TRANSFORMERS
from backend.core.protocols import VLMResult


@pytest.fixture
def mock_transformers():
    with patch("backend.models.qwen_vlm.HAS_TRANSFORMERS", True), \
         patch("backend.models.qwen_vlm.AutoProcessor") as mock_processor_cls, \
         patch("backend.models.qwen_vlm.Qwen2_5_VLForConditionalGeneration") as mock_model_cls, \
         patch("backend.models.qwen_vlm.BitsAndBytesConfig") as mock_bnb_cls, \
         patch("backend.models.qwen_vlm.process_vision_info") as mock_process_vision, \
         patch("torch.no_grad"):

        # Setup mock processor
        mock_processor_instance = MagicMock()
        mock_processor_instance.apply_chat_template.return_value = "mock_text_prompt"
        
        # Setup inputs mock
        mock_inputs = MagicMock()
        mock_inputs.to.return_value = mock_inputs
        mock_inputs.input_ids = [[1, 2, 3]]
        
        mock_processor_instance.return_value = mock_inputs
        mock_processor_instance.batch_decode.return_value = ["Mocked response text"]
        
        mock_processor_cls.from_pretrained.return_value = mock_processor_instance
        
        # Setup mock model
        mock_model_instance = MagicMock()
        mock_model_instance.device = "cuda:0"
        mock_model_instance.generate.return_value = [[1, 2, 3, 4, 5, 6]]
        
        mock_model_cls.from_pretrained.return_value = mock_model_instance
        
        # Setup vision info
        mock_process_vision.return_value = ([MagicMock()], None)
        
        yield {
            "processor": mock_processor_cls,
            "model": mock_model_cls,
            "bnb": mock_bnb_cls
        }


def test_qwen_vlm_lazy_loading(mock_transformers):
    vlm = QwenVLM()
    
    assert not vlm.is_loaded()
    assert vlm._model is None
    assert vlm._processor is None
    
    # ModelInfo should work even when not loaded
    info = vlm.get_model_info()
    assert info.name == "Qwen/Qwen2.5-VL-3B-Instruct"
    
    # Explicit load
    vlm.load()
    assert vlm.is_loaded()
    
    # Trigger load by calling predict
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    result = vlm.predict(image, "What is this?")
    
    assert vlm.is_loaded()
    assert vlm._model is not None
    assert vlm._processor is not None
    
    # Check if from_pretrained was called correctly (only once due to idempotent load)
    mock_transformers["model"].from_pretrained.assert_called_once()
    mock_transformers["processor"].from_pretrained.assert_called_once_with("Qwen/Qwen2.5-VL-3B-Instruct")
    
    # Unload
    vlm.unload()
    assert not vlm.is_loaded()
    assert vlm._model is None


def test_qwen_vlm_predict(mock_transformers):
    vlm = QwenVLM()
    
    # Test float image (should be normalized)
    image = np.random.rand(100, 100, 3).astype(np.float32)
    result = vlm.predict(image, "Find the road")
    
    assert isinstance(result, VLMResult)
    assert result.answer == "Mocked response text"
    
    # Confidence should be honestly unavailable
    assert result.confidence.value is None
    assert result.confidence.source == "unavailable"
    assert "calibrated" in result.confidence.method or "calibrated" in result.confidence.method.lower()
    
    assert len(result.evidence) == 1
    assert result.evidence[0].band_count == 3
    
    # Trace/timing should be present
    assert "inference_duration_ms" in result.raw_output


def test_qwen_vlm_missing_transformers():
    with patch("backend.models.qwen_vlm.HAS_TRANSFORMERS", False):
        vlm = QwenVLM()
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        
        with pytest.raises(RuntimeError, match="transformers.*required"):
            vlm.predict(image, "test")
