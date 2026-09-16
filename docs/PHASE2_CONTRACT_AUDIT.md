# Phase 2 Contract Audit

This document captures the state of the codebase prior to the Phase 2 stabilization refactor. It lists all identified mismatches between documentation, protocols, types, services, and API schemas.

## 1. Mismatched AnalysisResult Representation

**Issue:** The project lacks a single unified internal representation of an analysis result.

- `backend/core/types.py` defines an `AnalysisResult` dataclass, but it is currently dead code. No service returns it.
- `backend/api/schemas.py` defines `AnalysisResultSchema`.
- Services (`vqa.py`, `grounding.py`) currently return `AnalysisResultSchema` directly, bypassing an internal domain model.
- Other services (`change_detection.py`, `captioning.py`, `cross_modal.py`) attempt to return `AnalysisResult` but use incorrect fields that don't match `core/types.py`.

## 2. ExecutionStep Drift

**Issue:** The internal `ExecutionStep` is out of sync with the API representation.

- `backend/core/types.py`: `ExecutionStep(step_id, action, model_used, status, details, timestamp)`
- `backend/api/schemas.py`: `ExecutionStepSchema(step_number, action, status, duration_ms, observable_output)`

The API schema reflects the fields that are actually useful and used.

## 3. ConfidenceScore Literal Constraint

**Issue:** `ConfidenceScore.source` is overly constrained.

- `backend/core/confidence.py` types `source` as `Literal["model_logits", "calibrated", "evidence_agreement", "heuristic", "unavailable"]`.
- Various services construct confidence scores with sources like `"executor"` or `"fused"`, which violates the Literal type.

## 4. Evidence Constructor Mismatches

**Issue:** The `backend/core/evidence.py` definitions do not match how services attempt to construct them.

- **`ChangeMapEvidence`**:
  - `evidence.py`: `(change_mask_path, changed_area_percent, changed_regions, total_area_pixels, method, type)`
  - `change_detection.py` calls: `(source, confidence, mask_data, regions)`
- **`CrossModalAgreementEvidence`**:
  - `evidence.py`: `(optical_evidence, sar_evidence, agreement, agreement_score, explanation, type)`
  - `cross_modal.py` calls: `(source, confidence, agreement_level, supporting_optical, supporting_sar, conflict_details)`
- **`ChangedRegion`**:
  - `evidence.py`: `(polygon_coords, area_pixels, change_type)`
  - `change_detection.py` calls: `(centroid, area, bbox)`

## 5. Service Implementation Errors

**Issue:** Services in development (`change_detection.py`, `captioning.py`, `cross_modal.py`) contain broken protocol calls and property accesses.

- Attempting to access `image.id` instead of `image.image_id` on `RSDataObject`.
- Calling non-existent model methods (e.g., `model.generate_answer()` instead of `model.predict()`, `sar_analyzer.analyze_sar()` instead of the correct protocol method).

## 6. Query Route Monolith

**Issue:** `POST /api/v1/query` is heavily coupled to service instantiation and routing logic.

- `backend/api/routes.py` directly handles model instantiation, service creation, and routing.
- This needs to be decoupled into a lightweight orchestrator to prepare for the future agent/executor.

## 7. Misleading Executor Scaffolding

**Issue:** The current executor scaffolding generates fake success outputs.

- `backend/agents/executor.py` returns fake mock answers and confidence scores.
- This creates the illusion of working code and violates the "NO FAKE DEMOS" rule.
