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
    """Determine the intent of a query using basic heuristics."""
    query_lower = request.query.lower()
    
    # Simple grounding heuristic
    if re.search(r'\b(where|find|locate|show me|box|bounding)\b', query_lower):
        logger.info("Routed to GROUNDING based on keywords.")
        return QueryIntent.GROUNDING
        
    # Simple change detection heuristic
    if re.search(r'\b(change|difference|before and after|compare)\b', query_lower):
        logger.info("Routed to CHANGE_DETECTION based on keywords.")
        return QueryIntent.CHANGE_DETECTION
        
    # Default to VQA
    logger.info("Routed to VQA as default intent.")
    return QueryIntent.VQA
