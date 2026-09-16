"""Cached model representations that replay genuine prior model outputs.

Used for the Demo mode to avoid expensive live inference while maintaining
fully accurate and truthful execution traces.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Dict, Optional

import numpy as np

from backend.core.confidence import ConfidenceScore
from backend.core.evidence import BoundingBox, BoundingBoxEvidence
from backend.core.exceptions import SatQueryError
from backend.core.protocols import GroundingResult, ModelInfo, VLMResult
from backend.models.base import BaseModel

logger = logging.getLogger(__name__)


def compute_input_hash(image: np.ndarray, text: str) -> str:
    """Compute a deterministic hash for an image and text input pair."""
    # Using a fast hash over shape and partial content plus text
    h = hashlib.sha256()
    h.update(str(image.shape).encode())
    
    # Sample some bytes from the array if it's large enough
    if image.size > 1000:
        h.update(image.flat[0:1000].tobytes())
    else:
        h.update(image.tobytes())
        
    h.update(text.encode())
    return h.hexdigest()


class CachedOutputStore:
    """Store and retrieve pre-computed genuine model outputs."""
    
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    def load_cache(self) -> None:
        """Load all cached outputs from the cache directory."""
        if not os.path.exists(self.cache_dir):
            logger.warning(f"Cache directory {self.cache_dir} does not exist.")
            return
            
        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".json"):
                path = os.path.join(self.cache_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Assume data has a 'hash' field or use filename as hash
                        key = data.get("hash", filename.replace(".json", ""))
                        self._cache[key] = data
                except Exception as e:
                    logger.error(f"Failed to load cache file {path}: {e}")
                    
    def get_cached_output(self, model_name: str, input_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve a cached output."""
        # Simple lookup strategy; in a real app, model_name should be part of the key
        return self._cache.get(f"{model_name}_{input_hash}")
        
    def store_output(self, model_name: str, input_hash: str, output: Dict[str, Any]) -> None:
        """Store a new output into the cache and save to disk."""
        key = f"{model_name}_{input_hash}"
        self._cache[key] = output
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
            
        path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write cache file {path}: {e}")


class CachedVLM(BaseModel):
    """Replays genuine prior VLM outputs."""
    
    def __init__(self, name: str, cache_store: CachedOutputStore):
        super().__init__(name)
        self.cache_store = cache_store

    def load(self) -> None:
        self.cache_store.load_cache()
        self._loaded = True

    def unload(self) -> None:
        self._loaded = False

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            name=self.name,
            version="1.0-cached",
            backend_type="CACHED",
            description="Cached replayer for real VLM outputs.",
            device="cpu"
        )

    def predict(self, image: np.ndarray, prompt: str, **kwargs: Any) -> VLMResult:
        if not self.is_loaded():
            self.load()
            
        input_hash = compute_input_hash(image, prompt)
        cached_data = self.cache_store.get_cached_output(self.name, input_hash)
        
        if not cached_data:
            raise SatQueryError(f"No cached output found for input hash {input_hash}")
            
        confidence = ConfidenceScore.unavailable("Cached output — confidence not preserved")
        if "confidence" in cached_data:
            # Reconstruct confidence if available
            c_data = cached_data["confidence"]
            confidence = ConfidenceScore(
                value=c_data.get("value"),
                source=c_data.get("source", "unavailable"),
                method=c_data.get("method", "from cache"),
                calibrated=c_data.get("calibrated", False)
            )

        return VLMResult(
            answer=cached_data.get("answer", "Unknown cached answer."),
            evidence=[],  # Parsing complex evidence from cache would go here
            confidence=confidence,
            raw_output={"is_cached": True, "original_raw": cached_data.get("raw_output")}
        )


class CachedGroundingModel(BaseModel):
    """Replays genuine prior grounding model outputs."""
    
    def __init__(self, name: str, cache_store: CachedOutputStore):
        super().__init__(name)
        self.cache_store = cache_store

    def load(self) -> None:
        self.cache_store.load_cache()
        self._loaded = True

    def unload(self) -> None:
        self._loaded = False

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            name=self.name,
            version="1.0-cached",
            backend_type="CACHED",
            description="Cached replayer for real Grounding model outputs.",
            device="cpu"
        )

    def ground(self, image: np.ndarray, text_query: str, **kwargs: Any) -> GroundingResult:
        if not self.is_loaded():
            self.load()
            
        input_hash = compute_input_hash(image, text_query)
        cached_data = self.cache_store.get_cached_output(self.name, input_hash)
        
        if not cached_data:
            raise SatQueryError(f"No cached output found for input hash {input_hash}")
            
        # Reconstruct boxes
        boxes_data = cached_data.get("boxes", [])
        boxes = [BoundingBox(**b) for b in boxes_data]
        
        evidence = BoundingBoxEvidence(
            boxes=boxes,
            source_image_id="cached_image",
            model_source=self.name
        )
        
        confidence = ConfidenceScore.unavailable("Cached output")
        
        return GroundingResult(
            boxes=boxes,
            evidence=[evidence],
            confidence=confidence,
            raw_output={"is_cached": True, "original_raw": cached_data.get("raw_output")}
        )
