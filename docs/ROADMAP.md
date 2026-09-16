# Phase-Based Roadmap

**Note**: There are no day limits. Progress is milestone-driven.

## PHASE 0: Foundation
- **Objective**: Establish scaffolding, configurations, and core docs.
- **Prerequisites**: None.
- **Deliverables**: Docs (Architecture, API), FastAPI skeleton, Pytest config.
- **Tests**: API health check passes.
- **Completion Criteria**: Scaffolding complete, API serves `/health`.
- **Dependencies**: None.

## PHASE 1: Remote-Sensing Data Engine
- **Objective**: Build the preprocessing pipeline for GeoTIFFs.
- **Deliverables**: `preprocessing` module with RasterIO integration.
- **Tests**: Load valid/invalid GeoTIFFs, normalize to RGB.
- **Completion Criteria**: `RS DataObject` can be instantiated from file upload.
- **Risks**: CRS mismatches.

## PHASE 2: Core Intelligence Capabilities
- **Objective**: Implement VQA and Grounding abstract services.
- **Deliverables**: 3-tier model adapters (Mock/Cached/Real).
- **Tests**: Run MockModel for VQA and Grounding.
- **Completion Criteria**: End-to-end `/query` API works with MockModels.

## PHASE 3: Remote-Sensing Model Adaptation
- **Objective**: Fine-tune/LoRA the VLM on RS datasets.
- **Deliverables**: Training scripts, LoRA adapter weights.
- **Tests**: Compare zero-shot vs fine-tuned accuracy.
- **Completion Criteria**: Documented eval improvement (or fallback to zero-shot).

## PHASE 4: Agentic Orchestration
- **Objective**: Build hybrid router (Deterministic + LLM Planner).
- **Deliverables**: `agents` module handling complex queries.
- **Completion Criteria**: System successfully splits a multi-task query into separate service calls.

## PHASE 5: Evidence and Trust Layer
- **Objective**: Implement typed Evidence fusion.
- **Deliverables**: Evidence tracking dataclasses throughout pipeline.
- **Tests**: Validate response JSON has Confidence tracking.
- **Completion Criteria**: Never fabricating sources.

## PHASE 6: Bi-Temporal CD & Cross-Modal
- **Objective**: Enable optical-SAR comparison and CD.
- **Deliverables**: Siamese CNN adapter, cross-modal logic.
- **Risks**: Alignment issues between T1/T2.

## PHASE 7: Evaluation Framework
- **Objective**: Scripted rigorous testing of all models.
- **Deliverables**: `scripts/evaluate.py`.
- **Completion Criteria**: Benchmark outputs generated to `docs/evaluations/`.

## PHASE 8: Backend Productization
- **Objective**: Security, demo mode, and reliability.
- **Deliverables**: Cached output generation for demo, path traversal limits.
- **Completion Criteria**: Demo endpoints fully functional without GPU.

## PHASE 9: Frontend Integration Readiness
- **Objective**: Finalize API for UI teams.
- **Deliverables**: OpenAPI spec, CORS fine-tuning.
- **Completion Criteria**: Frontend can successfully upload and query.

## PHASE 10: Competition Optimization
- **Objective**: Final polish for SIH 2026.
- **Deliverables**: Pitch materials, architecture diagrams finalized.
