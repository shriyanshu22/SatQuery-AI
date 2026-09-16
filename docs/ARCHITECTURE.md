# Architecture: SatQuery AI (SIH26167)

## 1. System Overview and Design Philosophy
SatQuery AI is an agentic vision-language assistant for multimodal remote sensing image analysis. It leverages Large Vision-Language Models (VLMs) and specialized computer vision models to perform complex analyses on satellite imagery, including visual question answering (VQA), text-guided grounding, bi-temporal change detection, and cross-modal (Optical+SAR) analysis.

**Design Philosophy**:
- **Truth over Speculation**: The system must never fabricate model outputs, confidences, or evidence.
- **Modularity**: Every capability (VQA, grounding, CD) is backed by substitutable models.
- **Traceability**: All decisions and answers are backed by typed Evidence data objects.
- **Robustness**: The preprocessing engine handles the idiosyncrasies of remote sensing formats (GeoTIFFs, various CRSs) before they reach the model.

## 2. Layered Architecture Diagram

```text
+-----------------------------------------------------------------------------+
|                               API LAYER (FastAPI)                           |
|  [Endpoints: /query, /upload, /status, /result, /demo, /health]             |
+-----------------------------------------------------------------------------+
                                     |
+-----------------------------------------------------------------------------+
|                             AGENT LAYER (Hybrid)                            |
|  [Deterministic Rule Engine]  <--->  [Optional LLM Planner]                 |
|  [Query Decomposition]               [Task Orchestration]                   |
+-----------------------------------------------------------------------------+
                                     |
+-----------------------------------------------------------------------------+
|                              SERVICE LAYER                                  |
|  [VQA Service]  [Grounding Service]  [Change Detection]  [Cross-Modal]      |
|  (Evidence Aggregation & Confidence Attribution)                            |
+-----------------------------------------------------------------------------+
                                     |
+-----------------------------------------------------------------------------+
|                              MODEL LAYER (Tiered)                           |
|  <<Protocol>> ModelAdapter                                                  |
|  ├── RealModel (Live Inference)                                             |
|  ├── CachedModelOutput (Replay of genuine prior outputs)                    |
|  └── MockModel (Deterministic stubs for testing)                            |
+-----------------------------------------------------------------------------+
                                     |
+-----------------------------------------------------------------------------+
|                           PREPROCESSING LAYER                               |
|  [RasterIO Reader]  [Patching/Tiling]  [Normalization]  [Format Adapters]   |
+-----------------------------------------------------------------------------+
                                     |
+-----------------------------------------------------------------------------+
|                                CORE LAYER                                   |
|  [Evidence DataObjects]  [Confidence Types]  [Base Configurations]          |
+-----------------------------------------------------------------------------+
```

## 3. Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `api` | FastAPI application, dependency injection, endpoint definitions, Pydantic v2 schemas. |
| `agents` | Query routing, task decomposition, orchestrating multi-step plans. Hybrid approach. |
| `services` | Domain logic for VQA, grounding, etc. Evidence fusion and formatting. |
| `models` | Protocols and concrete adapters for specific AI models (e.g., Qwen2-VL, Grounding DINO). |
| `preprocessing`| Reading/writing GeoTIFFs via `rasterio`, CRS handling, image normalization. |
| `core` | Domain primitives. Isolated; imports nothing else. Contains Evidence/Confidence classes. |
| `utils` | Shared utilities, logging configurations (`structlog`), formatting helpers. |
| `evaluation`| Benchmarking and metric tracking scripts (isolated from runtime). |

## 4. Dependency Boundaries
- `core` is the base layer. It cannot import from `models`, `services`, `api`, etc.
- `preprocessing` can import from `core` but not from `models` or `services`.
- `models` can import `preprocessing` and `core`.
- `services` coordinates `models`.
- `agents` coordinates `services`.
- `api` is the presentation layer; it wires dependencies together.

## 5. Model Abstraction Strategy
All models adhere to a `typing.Protocol`.
Three-tier approach guarantees stability and honest demos:
1. **RealModel**: Wraps an actual PyTorch/Transformers model pipeline.
2. **CachedModelOutput**: Returns pre-computed, *genuine* outputs from a RealModel for specific hashes.
3. **MockModel**: Fully deterministic responses, strictly for unit tests.

## 6. Agent Architecture (Hybrid Routing)
The Agent uses a hybrid routing strategy:
- **Deterministic Rule Engine**: Matches queries to single capabilities based on regex/keywords for speed.
- **LLM Planner**: For complex queries ("Did urban development increase and can SAR confirm?"), an LLM generates a sub-task DAG, executes them via services, and fuses evidence.

## 7. Evidence & Confidence System
- **Evidence**: `dataclass`es representing bounding boxes, text answers, masks, and change maps. Must include source tracking.
- **Confidence**: `dataclass` containing a float [0, 1] and a `source` string. If confidence is unavailable, `value=None`, `source="unavailable"`, with `explanation`.

## 8. Security & Data
- Inputs: Validated strictly via Pydantic. File uploads checked for magic numbers and malicious paths.
- Outputs: No execution traces returned to the user unless in debug mode.

## 9. Key Design Decisions
- **Decision 1:** Decouple ML models from domain logic. *Rationale*: Allows swapping Qwen2-VL for Qwen2.5-VL with zero changes to the VQA service.
- **Decision 2:** Core has no dependencies. *Rationale*: Prevents circular imports when passing Evidence objects between layers.
- **Decision 3:** Frontend separation. *Rationale*: Enables parallel development tracks.
