"""Lightweight orchestration for the query API.

This module provides a boundary between the HTTP routes and the service logic,
acting as a placeholder for the future agentic planner (Phase 4).
"""

from __future__ import annotations

from backend.core.types import QueryIntent, RSDataObject, AnalysisResult
from backend.api.schemas import QueryRequest
from backend.agents.router import route_query
from backend.preprocessing.adapters import VLMAdapter, GroundingAdapter
from backend.models.mock_vlm import MockVLM, MockGroundingModel
from backend.services.vqa import VQAService
from backend.services.grounding import GroundingService


class QueryOrchestrator:
    """Orchestrates query execution across services."""

    def execute(self, request: QueryRequest, image: RSDataObject) -> AnalysisResult:
        """
        Route the query, instantiate the appropriate service and mock model,
        and execute the analysis.
        """
        intent = route_query(request)
        
        if intent == QueryIntent.GROUNDING:
            adapter = GroundingAdapter()
            model = MockGroundingModel()
            service = GroundingService(model, adapter)
            # Handle possible naming mismatch (locate_objects vs ground_query)
            if hasattr(service, "locate_objects"):
                return service.locate_objects(image, request.query)
            elif hasattr(service, "ground_query"):
                return service.ground_query(image, request.query) # fallback if name differs
            else:
                raise AttributeError("GroundingService missing execution method.")
        else:
            # Default to VQA for now
            adapter = VLMAdapter((1024, 1024))
            model = MockVLM()
            service = VQAService(model, adapter)
            return service.answer_question(image, request.query)
