from __future__ import annotations

from typing import Any
import numpy as np

from backend.core.types import RSDataObject
from backend.core.exceptions import PreprocessingError
from backend.preprocessing.normalizer import to_uint8
from backend.preprocessing.sar import detect_sar_image, preprocess_sar
from backend.core.logging import get_logger

logger = get_logger(__name__)


class ModelAdapter:
    """Base class for adapting RSDataObject to model-specific formats."""
    def adapt(self, rs_data: RSDataObject) -> Any:
        raise NotImplementedError("Subclasses must implement adapt()")


class VLMAdapter(ModelAdapter):
    """Adapter for Vision-Language Models (typically expects RGB images)."""
    def __init__(self, target_size: tuple[int, int] | None = None):
        self.target_size = target_size

    def adapt(self, rs_data: RSDataObject) -> Any:
        logger.debug(f"Adapting {rs_data.image_id} for VLM")
        data = rs_data.data
        
        # Ensure it's 3-channel RGB (mocking logic)
        if len(data.shape) == 3 and data.shape[0] > 3:
            # Taking first 3 bands as a naive fallback
            data = data[:3, :, :]
            
        return to_uint8(data)


class GroundingAdapter(ModelAdapter):
    """Adapter for text-guided grounding models."""
    def adapt(self, rs_data: RSDataObject) -> Any:
        logger.debug(f"Adapting {rs_data.image_id} for Grounding Model")
        # Typically needs specific normalization
        return to_uint8(rs_data.data)


class ChangeDetectionAdapter(ModelAdapter):
    """Adapter for Change Detection (handles temporal pairs)."""
    def adapt_pair(self, before: RSDataObject, after: RSDataObject) -> tuple[Any, Any]:
        logger.debug(f"Adapting temporal pair {before.image_id} and {after.image_id} for Change Detection")
        if before.data.shape != after.data.shape:
            raise PreprocessingError("Before and After images must have the same shape for change detection.")
        return before.data, after.data
        
    def adapt(self, rs_data: RSDataObject) -> Any:
        # For single image adaptations if needed
        return rs_data.data


class SARAdapter(ModelAdapter):
    """Adapter for SAR specialized models."""
    def adapt(self, rs_data: RSDataObject) -> Any:
        logger.debug(f"Adapting {rs_data.image_id} for SAR model")
        if detect_sar_image(rs_data):
            processed = preprocess_sar(rs_data)
            return processed.data
        return rs_data.data


def get_adapter(model_type: str) -> ModelAdapter:
    """Factory function for retrieving model adapters."""
    adapters = {
        "vlm": VLMAdapter(),
        "grounding": GroundingAdapter(),
        "change_detection": ChangeDetectionAdapter(),
        "sar": SARAdapter()
    }
    adapter = adapters.get(model_type.lower())
    if not adapter:
        raise ValueError(f"Unknown model type for adapter: {model_type}")
    return adapter
