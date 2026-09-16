"""Lightweight orchestration for the query API.

This module provides a boundary between the HTTP routes and the service logic,
acting as a placeholder for the future agentic planner (Phase 4).

It selects between REAL and MOCK model backends based on ``Settings.model.backend_type``.
"""

from __future__ import annotations

import threading
from typing import Any

from backend.core.config import Settings, get_settings
from backend.core.types import QueryIntent, RSDataObject, AnalysisResult
from backend.api.schemas import QueryRequest
from backend.agents.router import route_query
from backend.preprocessing.adapters import VLMAdapter, GroundingAdapter
from backend.models.mock_vlm import MockVLM, MockGroundingModel
from backend.services.vqa import VQAService
from backend.services.grounding import GroundingService
from backend.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton for the heavy real VLM model.
# Loaded once on first REAL request, reused for the process lifetime.
# ---------------------------------------------------------------------------
_real_vlm_instance: Any = None
_real_vlm_lock = threading.Lock()


def _get_real_vlm() -> Any:
    """Return the singleton QwenVLM instance, loading it on first call.

    Thread-safe via a module-level lock so concurrent requests don't
    trigger duplicate model loads.
    """
    global _real_vlm_instance
    if _real_vlm_instance is not None:
        return _real_vlm_instance

    with _real_vlm_lock:
        # Double-checked locking
        if _real_vlm_instance is not None:
            return _real_vlm_instance

        from backend.models.qwen_vlm import QwenVLM

        logger.info("Initialising singleton QwenVLM for REAL backend...")
        instance = QwenVLM()
        instance.load()
        _real_vlm_instance = instance
        return _real_vlm_instance


class QueryOrchestrator:
    """Orchestrates query execution across services.

    Args:
        settings: Application settings. When ``None``, falls back to
            the cached ``get_settings()`` singleton.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def execute(self, request: QueryRequest, image: RSDataObject | list[RSDataObject]) -> AnalysisResult:
        """Route the query, instantiate the appropriate service and model,
        and execute the analysis.

        Args:
            request: The incoming query request.
            image: A single RSDataObject or list of RSDataObjects.

        Returns:
            Canonical AnalysisResult.
        """
        images: list[RSDataObject] = image if isinstance(image, list) else [image]
        primary_image = images[0]
        intent = route_query(request)
        backend = self.settings.model.backend_type.upper()

        logger.info(f"Orchestrating query with intent={intent}, backend={backend}, num_images={len(images)}")

        # 1. Multi-image: Cross-Modal Analysis (Optical + SAR)
        if intent == QueryIntent.CROSS_MODAL and len(images) >= 2:
            from backend.services.cross_modal import CrossModalAnalysisService
            logger.info("Executing CrossModalAnalysisService for multi-sensor query.")
            # Find optical and SAR if possible, otherwise use images[0] and images[1]
            opt_img = next((img for img in images if getattr(img.metadata, 'modality', '').lower() == 'optical'), images[0])
            sar_img = next((img for img in images if getattr(img.metadata, 'modality', '').lower() == 'sar'), images[1])
            service = CrossModalAnalysisService(vlm_model=MockVLM(), sar_analyzer=None)
            return service.analyze(optical_image=opt_img, sar_image=sar_img, query=request.query)

        # 2. Multi-image: Bi-temporal Change Detection
        if intent == QueryIntent.CHANGE_DETECTION and len(images) >= 2:
            from backend.services.change_detection import ChangeDetectionService
            logger.info("Executing ChangeDetectionService for bi-temporal query.")
            adapter = VLMAdapter((1024, 1024))
            service = ChangeDetectionService(change_model=None, vlm_model=MockVLM(), adapter=adapter)
            return service.detect_changes(image_before=images[0], image_after=images[1], query=request.query)

        # 3. Single-image: Grounding
        if intent == QueryIntent.GROUNDING:
            adapter = GroundingAdapter()
            model = MockGroundingModel()
            service = GroundingService(model, adapter)
            if hasattr(service, "locate_objects"):
                return service.locate_objects(primary_image, request.query)
            elif hasattr(service, "ground_query"):
                return service.ground_query(primary_image, request.query)
            else:
                raise AttributeError("GroundingService missing execution method.")

        # 4. Default / Single-image: Visual Question Answering
        adapter = VLMAdapter((1024, 1024))

        if backend == "REAL":
            logger.info("Using REAL Qwen VLM backend for VQA.")
            model = _get_real_vlm()
        else:
            logger.info(f"Using MOCK VLM backend for VQA (backend_type={backend}).")
            model = MockVLM()

        service = VQAService(model, adapter)
        return service.answer_question(primary_image, request.query)

