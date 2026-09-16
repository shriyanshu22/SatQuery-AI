"""Grounding DINO adapter for text-guided object detection.

Real inference implementation that loads ``IDEA-Research/grounding-dino-tiny``
and conforms to both ``GroundingProtocol`` and the ``BaseModel`` lifecycle.
"""

from __future__ import annotations

import os
import time
from typing import Any

import numpy as np
from PIL import Image

from backend.core.confidence import ConfidenceScore
from backend.core.evidence import BoundingBox, Evidence, MetadataEvidence
from backend.core.logging import get_logger
from backend.core.protocols import GroundingProtocol, GroundingResult, ModelInfo
from backend.models.base import BaseModel

logger = get_logger(__name__)

# Try importing transformers; allow graceful fallback for tests/CI.
try:
    import torch
    from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


class GroundingDINOModel(BaseModel, GroundingProtocol):
    """Grounding DINO (Tiny) for zero-shot, text-guided object detection.

    Loads lazily in FP16 on the first ``ground()`` call.  The model is
    lightweight (~340 MB) and fits comfortably alongside QwenVLM on a
    6 GB RTX 4050 Laptop GPU.
    """

    DEFAULT_MODEL_ID = "IDEA-Research/grounding-dino-tiny"

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        name: str = "grounding-dino-tiny",
        box_threshold: float = 0.30,
        text_threshold: float = 0.25,
    ) -> None:
        """Initialise the adapter.

        Args:
            model_id: HuggingFace model identifier.
            name: Human-readable name for logs and metadata.
            box_threshold: Minimum score to keep a detection.
            text_threshold: Minimum text-matching score.
        """
        super().__init__(name)
        self.model_id = model_id
        self.box_threshold = box_threshold
        self.text_threshold = text_threshold
        self._model: Any = None
        self._processor: Any = None

    # ------------------------------------------------------------------
    # BaseModel lifecycle
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load the model into GPU/CPU memory."""
        self._load_model()
        self._loaded = True

    def unload(self) -> None:
        """Unload the model from memory to free VRAM."""
        if self._model is not None:
            del self._model
            self._model = None
        if self._processor is not None:
            del self._processor
            self._processor = None
        self._loaded = False
        if HAS_TRANSFORMERS and torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info(f"Model {self.model_id} unloaded.")

    def is_loaded(self) -> bool:
        """Check if the model is currently loaded in memory."""
        return self._model is not None

    # ------------------------------------------------------------------
    # Internal loading
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """Download / load model weights (idempotent)."""
        if not HAS_TRANSFORMERS:
            raise RuntimeError(
                "transformers and torch are required for GroundingDINOModel."
            )

        if self._model is not None:
            return

        logger.info(f"Loading {self.model_id}...")

        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

        device = "cuda" if torch.cuda.is_available() else "cpu"

        self._processor = AutoProcessor.from_pretrained(self.model_id)
        self._model = AutoModelForZeroShotObjectDetection.from_pretrained(
            self.model_id,
        ).to(device)

        logger.info(
            f"Model {self.model_id} loaded on {device}."
        )

    # ------------------------------------------------------------------
    # GroundingProtocol
    # ------------------------------------------------------------------

    def get_model_info(self) -> ModelInfo:
        """Get metadata about this model."""
        device = None
        if self._model is not None and hasattr(self._model, "device"):
            device = str(self._model.device)

        return ModelInfo(
            name=self.model_id,
            version="tiny",
            backend_type="transformers_fp16",
            description="Grounding DINO Tiny for zero-shot text-guided object detection.",
            device=device,
        )

    def ground(
        self, image: np.ndarray, text_query: str, **kwargs: Any
    ) -> GroundingResult:
        """Locate objects matching ``text_query`` in ``image``.

        Args:
            image: Image as numpy array — either ``(H, W, 3)`` uint8 or
                ``(C, H, W)`` in the remote-sensing convention.
            text_query: Natural-language description of objects to find,
                e.g. ``"buildings"``.
            **kwargs: Reserved for future options.

        Returns:
            GroundingResult with real bounding boxes, evidence, and timing.
        """
        self._load_model()

        if not HAS_TRANSFORMERS:
            raise RuntimeError("Transformers is not installed.")

        # --- Prepare PIL image -------------------------------------------
        if image.dtype != np.uint8:
            if image.max() <= 1.0:
                img_array = (image * 255).astype(np.uint8)
            else:
                img_array = image.astype(np.uint8)
        else:
            img_array = image

        # Transpose (C, H, W) → (H, W, C) if needed
        if len(img_array.shape) == 3 and img_array.shape[0] in (1, 3, 4):
            img_array = np.transpose(img_array, (1, 2, 0))
            if img_array.shape[2] == 1:
                img_array = img_array[:, :, 0]

        pil_image = Image.fromarray(img_array)
        img_w, img_h = pil_image.size

        # --- Normalise the query for Grounding DINO ----------------------
        # Grounding DINO expects labels separated by " . " and ending
        # with " ." — e.g. "building . road ."
        normalised_query = self._normalise_query(text_query)

        # --- Run inference -----------------------------------------------
        inputs = self._processor(
            images=pil_image,
            text=normalised_query,
            return_tensors="pt",
        ).to(self._model.device)

        t0 = time.perf_counter()
        with torch.no_grad():
            outputs = self._model(**inputs)
        inference_ms = (time.perf_counter() - t0) * 1000.0

        # --- Post-process ------------------------------------------------
        results = self._processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            threshold=self.box_threshold,
            text_threshold=self.text_threshold,
            target_sizes=[(img_h, img_w)],
        )

        # Extract detections from the first (only) image
        det = results[0]
        scores = det["scores"].cpu().tolist()
        labels = det["labels"]
        boxes_tensor = det["boxes"].cpu()  # (N, 4) in [x1, y1, x2, y2]

        # Build canonical BoundingBox list
        bounding_boxes: list[BoundingBox] = []
        for i, (score, label) in enumerate(zip(scores, labels)):
            x1, y1, x2, y2 = boxes_tensor[i].tolist()
            bounding_boxes.append(
                BoundingBox(
                    x=x1,
                    y=y1,
                    w=x2 - x1,
                    h=y2 - y1,
                    label=str(label),
                    confidence=round(score, 4),
                )
            )

        # --- Confidence ---------------------------------------------------
        if bounding_boxes:
            # Use the maximum detection score as the overall confidence.
            max_score = max(b.confidence for b in bounding_boxes)
            conf = ConfidenceScore.from_model_logits(
                max_score,
                "Grounding DINO detection score (max across detections)",
            )
        else:
            conf = ConfidenceScore.unavailable(
                "No objects detected above the confidence threshold."
            )

        # --- Metadata evidence from inference ----------------------------
        evidence_list: list[Evidence] = [
            MetadataEvidence(
                source_file="inference",
                crs=None,
                resolution=None,
                bounds=None,
                band_count=img_array.shape[-1] if len(img_array.shape) > 2 else 1,
                acquisition_date=None,
            )
        ]

        return GroundingResult(
            boxes=bounding_boxes,
            evidence=evidence_list,
            confidence=conf,
            raw_output={
                "model_id": self.model_id,
                "inference_duration_ms": round(inference_ms, 2),
                "num_detections": len(bounding_boxes),
                "box_threshold": self.box_threshold,
                "text_threshold": self.text_threshold,
                "normalised_query": normalised_query,
                "image_size": [img_w, img_h],
            },
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise_query(text_query: str) -> str:
        """Normalise a natural-language query into Grounding DINO label format.

        Grounding DINO expects labels separated by `` . `` and ending
        with `` .``, e.g. ``"building . road ."``.

        This method strips common spatial question prefixes like
        ``"where are the"`` and ``"locate the"`` so that the model
        receives clean object names.

        Args:
            text_query: Raw user query.

        Returns:
            Formatted label string.
        """
        q = text_query.lower().strip().rstrip("?").strip()

        # Strip common question prefixes
        prefixes = [
            "where are the",
            "where is the",
            "where are",
            "where is",
            "locate the",
            "locate all",
            "locate",
            "find the",
            "find all",
            "find",
            "show me the",
            "show me",
            "detect the",
            "detect all",
            "detect",
            "identify the",
            "identify all",
            "identify",
        ]
        for prefix in prefixes:
            if q.startswith(prefix):
                q = q[len(prefix) :].strip()
                break

        # If already has the " . " separator, leave it alone
        if " . " in q or q.endswith("."):
            return q if q.endswith(".") else q + " ."

        # Otherwise treat as a single label
        return q + " ."
