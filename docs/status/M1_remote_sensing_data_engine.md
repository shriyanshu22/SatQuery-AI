# Milestone 1: Remote-Sensing Data Engine

**Status**: COMPLETED
**Date**: 2026-09-14
**Phase**: 1

## Overview

The Remote-Sensing Data Engine has been successfully implemented, establishing the core data processing pipeline for SatQuery AI. This component ensures that incoming remote-sensing data (GeoTIFFs, TIFFs, PNGs, JPEGs) is safely ingested, validated, and transformed into a model-agnostic `RSDataObject` without ever silently altering the user's original data.

## Accomplishments

### 1. Core Types Expansion
- Enriched `RSMetadata` and `RSDataObject` (in `backend/core/types.py`) to include explicit tracking of `image_id`, `original_filename`, `file_format`, `modality`, `validation_status`, `warnings`, and a rigorous `preprocessing_history`.
- Introduced `Modality` (Optical, Multispectral, SAR, Unknown) and `ValidationStatus` (Valid, Valid with Warnings, Invalid) enumerations.

### 2. Artifact Storage System
- Implemented `ArtifactStore` (in `backend/core/artifacts.py`) to manage derived outputs (previews, normalized images, tiles).
- Artifacts are logically grouped by `source_image_id`, maintaining traceability and keeping raw server paths isolated from the API client.

### 3. File Loading & Format Support
- Integrated `rasterio` for GeoTIFF extraction and `Pillow` for standard images (in `backend/preprocessing/image_loader.py`).
- Implemented robust format detection using extension and magic byte verification.
- Metadata extraction safely handles missing CRS or spatial transforms, emitting warnings rather than hard failures.

### 4. Validation Engine
- Created structured validation returning `ValidationResult` (in `backend/preprocessing/validators.py`).
- Pre-upload validation ensures MIME types, extensions, and file sizes are respected.
- Image validation detects corruption, exotic data types, and bounds/resolution issues.
- Added temporal and cross-modal pair compatibility checkers (e.g., checking spatial bounds overlap).

### 5. Modality Detection
- Implemented conservative modality detection heuristics (in `backend/preprocessing/modality.py`).
- Relies exclusively on reliable metadata (SAR band names, sensor keywords, band counts). Defaults to `UNKNOWN` if ambiguous, preventing incorrect processing pipelines down the line.

### 6. Preview Generation
- Developed an artifact-based preview generator (in `backend/preprocessing/preview.py`).
- Intelligently downsamples large imagery via windowed reading or Pillow resizing.
- Automatically selects visualization strategies (Grayscale, RGB composites, Log-scaled SAR) and normalizes dynamically using percentile clipping for optimal visual fidelity.

### 7. Spatial Operations & Alignment
- Engineered robust spatial utilities (in `backend/preprocessing/spatial.py`) for bounds overlap calculation and CRS compatibility.
- Re-wrote `alignment.py` to use `rasterio.warp.reproject` for real in-memory image reprojection and alignment.
- Overhauled `tiling.py` to support `rasterio.windows.Window` reading, allowing safe traversal of massive GeoTIFFs without memory exhaustion.

### 8. SAR Preprocessing
- Upgraded the SAR preprocessing pipeline (in `backend/preprocessing/sar.py`).
- Implemented standard log-scaling and an approximate Lee speckle filter (via `scipy.ndimage.uniform_filter`), isolating visual preprocessing from scientific preprocessing.

### 9. API Integration
- Added schemas for metadata, validation results, and upload responses (in `backend/api/schemas.py`).
- Implemented `POST /api/v1/upload` (in `backend/api/routes.py`) that executes the entire preprocessing pipeline on uploaded files.
- Added `GET /api/v1/artifacts/{artifact_id}` to securely serve generated preview files.

### 10. Testing
- Over 57 tests executed successfully. The stub implementations were upgraded to real function implementations while maintaining full backward compatibility.
- Zero failures in the `backend/tests` suite.

## Bug Fixes & Verifications

### File Persistence & Lookup Bug (2026-09-14)
- **Bug**: The upload endpoint `POST /api/v1/upload` saved files using their original filenames instead of the generated `image_id` UUID. The query endpoint then failed (returning 404) because it correctly expected to resolve images via the UUID as the authoritative key.
- **Fix**: Modified `backend/api/routes.py` to persist files as `{image_id}_{safe_filename}` and modified the query endpoint to scan for prefixes matching the provided `image_id`. We updated `load_image` across `image_loader.py` to accept an explicit `image_id` to prevent the internal `RSDataObject` from recalculating a UUID5 based on the file path. 
- **Tests**: Replaced mock upload tests in `test_api.py` with strict persistence, retrieval, and path traversal unit tests. 
- **Verification**: Executed a real end-to-end live test by uploading `data/demo/B02.tif` to a local FastAPI instance and subsequently querying it via the VQA pipeline. The test was 100% successful with correctly generated UUIDs propagated accurately into the `RSDataObject` and the VLM output trace.

## Next Steps

With Phase 1 and the critical persistence bug fixed, the backend is capable of digesting real remote sensing imagery. 

Proceed to **Phase 2: Agentic Execution Planner**, which will introduce the deterministic rule engine and LLM planning fallback to route user intents to the appropriate model adapters.
