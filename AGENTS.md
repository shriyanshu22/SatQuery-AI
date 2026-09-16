# Agent Instructions for SatQuery AI

**Project Context**: This project is for Smart India Hackathon 2026 (SIH26167), built by first-year engineering students.

## ABSOLUTE RULES

2. **NO FRONTEND**: Do NOT implement frontend code. We build the backend ONLY.
3. **NO FABRICATION**: Do NOT fabricate model outputs, confidence, evidence, metadata, or successful execution. If confidence is unavailable, value=None and source="unavailable" with an explanation.
4. **NO HIDDEN THOUGHTS**: Do NOT expose chain-of-thought in execution traces. Traces must contain only observable system actions.
5. **NO FAKE DEMOS**: Do NOT hard-code fake AI responses for demo mode. Use the real pipeline with mock deterministic outputs or cached real outputs.
6. **NO CIRCULAR DEPENDENCIES**: Keep module dependencies unidirectional.
7. **DEPENDENCY ORDER**: `api` → `agents` → `services` → `models` → `preprocessing` → `core`.
8. **PYTHON FUTURE**: All Python files must have `from __future__ import annotations`.
9. **DOCUMENTATION**: All public functions must have type hints and docstrings.
10. **PROTOCOLS**: Use protocols (`typing.Protocol`) for model abstraction.

## ARCHITECTURE RULES
- **Three Model Tiers**:
  - `RealModel`: Live inference using ML libraries (e.g., PyTorch, Transformers).
  - `MockModel`: Deterministic stub for testing and demoing without hardware.
  - `CachedModelOutput`: Replays real prior outputs.
- **Evidence**: First-class concept. Use typed dataclasses. Never use free-form strings for evidence.
- **Confidence**: Typed with source attribution.
- **Preprocessing**: Must be model-agnostic with per-model adapters.
- **Agent Routing**: Use deterministic rule engine as safe fallback, LLM planner is optional.

## CODE STYLE
- Python 3.10+, dataclasses, Pydantic v2, FastAPI.
- Google-style docstrings.
- `snake_case` for files, functions, variables.
- `PascalCase` for classes.

## TESTING RULES
- Tests must be in `backend/tests/`.
- Use `pytest`.
- Mock models for testing; tests should never require a GPU.

## FILE LOCATIONS
- Config: `configs/`
- Docs: `docs/`
- Data: `data/` (gitignored large files)
- Outputs: `outputs/` (gitignored)
