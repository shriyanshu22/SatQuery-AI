"""Query Router.

Temporary deterministic router for Phase 2. 
Will be replaced by a Hybrid Agent (Deterministic + LLM Planner) in Phase 4.
"""

from __future__ import annotations

import re

from backend.core.logging import get_logger
from backend.core.types import QueryIntent
from backend.api.schemas import QueryRequest

logger = get_logger(__name__)


def route_query(request: QueryRequest) -> QueryIntent:
    """Determine the intent of a query using multi-modal and keyword heuristics."""
    query_lower = request.query.lower()
    num_images = len(request.image_ids) if request.image_ids else 0

    # Cross-modal SAR + Optical heuristic
    if re.search(r'\b(optical and sar|sar|radar|corroborat|coherence|microwave|backscatter)\b', query_lower):
        logger.info("Routed to CROSS_MODAL based on SAR/radar keywords.")
        return QueryIntent.CROSS_MODAL

    # Change detection heuristic
    if re.search(r'\b(change|difference|before and after|compare|expansion|increased|decreased|growth)\b', query_lower) or num_images >= 2:
        logger.info("Routed to CHANGE_DETECTION based on keywords or multiple images.")
        return QueryIntent.CHANGE_DETECTION

    # Grounding heuristic
    if re.search(r'\b(where|find|locate|show me|box|bounding|detect|identify objects)\b', query_lower):
        logger.info("Routed to GROUNDING based on keywords.")
        return QueryIntent.GROUNDING

    # Default to VQA
    logger.info("Routed to VQA as default intent.")
    return QueryIntent.VQA

