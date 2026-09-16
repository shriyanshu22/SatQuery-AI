# Phase 2 Contract Stabilization

This document describes the stabilized contracts and boundaries established in Phase 2 for the SatQuery AI backend.

## Canonical AnalysisResult

The core internal representation of an AI analysis is the `AnalysisResult` dataclass defined in `backend/core/types.py`. All service modules (`vqa.py`, `grounding.py`, etc.) MUST return this type.

```python
@dataclass
class AnalysisResult:
    answer: str
    confidence: ConfidenceScore | None
    evidence: list[Evidence]
    execution_trace: list[ExecutionStep]
    metadata: dict[str, Any]
    warnings: list[str]
    errors: list[str]
    intent: QueryIntent
```

This internal result is then converted at the API boundary to `AnalysisResultSchema` before being sent to the client.

## ExecutionStep

The execution trace is composed of `ExecutionStep` objects, which track the observable actions taken by the system.

```python
@dataclass
class ExecutionStep:
    step_number: int
    action: str
    status: Literal["completed", "failed", "skipped"]
    duration_ms: float | None
    observable_output: str | None
```

## Confidence and Evidence

- **ConfidenceScore**: The `source` field is an open string to accommodate various sources without constantly changing the literal constraints. However, standard sources like `"model_logits"`, `"evidence_agreement"`, and `"unavailable"` are still encouraged.
- **Evidence**: Evidence classes (e.g., `BoundingBoxEvidence`, `ChangeMapEvidence`) are strict dataclasses. Services must instantiate them with the exact fields specified in `backend/core/evidence.py`.

## Service Contracts

Services encapsulate domain logic (VQA, Grounding, Change Detection).
- **Input**: `RSDataObject`, query text, and necessary models.
- **Output**: `AnalysisResult`.
- **Constraint**: Services DO NOT import from `backend.api.schemas`.

## The Orchestrator Boundary

The `POST /api/v1/query` endpoint delegates execution to a lightweight `QueryOrchestrator` in `backend/api/orchestrator.py`.
The orchestrator is responsible for:
1. Routing the query to determine the `QueryIntent`.
2. Selecting and instantiating the appropriate mock model.
3. Passing the data and model to the appropriate service.
4. Returning the canonical `AnalysisResult`.

This isolates the HTTP layer from the business logic.

## Executor Scaffolding

The files in `backend/agents/` (`executor.py`, `planner.py`, `registry.py`) are **Phase 4 scaffolding**. They are currently inactive and must not produce fake "success" outputs. They represent the future home of the autonomous agent layer.

## Three Model Tiers

The `backend/models` structure supports three tiers of model integration:
1. **RealModel**: Live inference (not yet implemented).
2. **CachedModelOutput**: Replays genuine prior outputs deterministically for demo and testing.
3. **MockModel**: Fast, rule-based deterministic stubs for CI/CD and basic contract validation (`mock_vlm.py`, `mock_grounding.py`). These are purely test stubs and do not perform actual ML inference.
