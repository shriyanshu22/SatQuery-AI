"""Shared type definitions and data structures.

This module defines the foundational data types used throughout the SatQuery AI
backend.  It lives in ``core`` and must not import from any other backend layer
(models, services, api, agents, preprocessing).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

import numpy as np

from backend.core.confidence import ConfidenceScore
from backend.core.evidence import Evidence


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Modality(str, Enum):
    """Detected imaging modality of a remote-sensing product.

    Modality is determined conservatively — if the detection algorithm cannot
    reliably classify the data, ``UNKNOWN`` is used and a warning is attached.
    """

    OPTICAL = "optical"
    """Standard RGB or pan-chromatic optical imagery."""

    MULTISPECTRAL = "multispectral"
    """Imagery with more than three spectral bands (e.g. Sentinel-2)."""

    SAR = "sar"
    """Synthetic Aperture Radar imagery."""

    UNKNOWN = "unknown"
    """Modality could not be determined reliably from available metadata."""


class ValidationStatus(str, Enum):
    """Outcome category of the file-validation pipeline.

    - ``VALID``: imagery passes all checks.
    - ``VALID_WITH_WARNINGS``: imagery is usable but has non-fatal issues
      (e.g. missing CRS or acquisition timestamp).
    - ``INVALID``: imagery cannot be used (corrupt, unsupported format, etc.).
    """

    VALID = "valid"
    VALID_WITH_WARNINGS = "valid_with_warnings"
    INVALID = "invalid"


class ModelBackend(str, Enum):
    """Types of available model backends."""

    REAL = "REAL"
    MOCK = "MOCK"
    CACHED = "CACHED"


class QueryIntent(str, Enum):
    """Categorized intents for user queries."""

    VQA = "VQA"
    GROUNDING = "GROUNDING"
    CHANGE_DETECTION = "CHANGE_DETECTION"
    SAR_ANALYSIS = "SAR_ANALYSIS"
    CROSS_MODAL = "CROSS_MODAL"
    CAPTIONING = "CAPTIONING"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Remote-Sensing Metadata
# ---------------------------------------------------------------------------

@dataclass
class RSMetadata:
    """Metadata extracted from a remote-sensing file.

    Design rationale for each field:

    * ``crs`` — Coordinate Reference System string (e.g. ``"EPSG:4326"``).
      Essential for spatial analysis and reprojection.
    * ``transform`` — Affine geo-transform mapping pixel ↔ world coords.
    * ``bounds`` — Geographic bounding box ``(left, bottom, right, top)``.
    * ``resolution`` — Ground sampling distance ``(x_res, y_res)`` in CRS
      units.  Needed for compatibility checking between image pairs.
    * ``band_count`` — Number of spectral bands.
    * ``band_names`` — Human-readable names for each band (e.g. ``["B02",
      "B03", "B04"]``).  ``None`` when not available.
    * ``dtype`` — NumPy-compatible data-type string (e.g. ``"uint8"``).
    * ``nodata`` — Sentinel value used by the raster for "no data" pixels.
    * ``width``, ``height`` — Raster dimensions in pixels.
    * ``file_format`` — Detected file format (``"geotiff"``, ``"tiff"``,
      ``"png"``, ``"jpeg"``).
    * ``acquisition_date`` — ISO-8601 timestamp when the data was captured.
      ``None`` when unavailable; a validation warning is emitted.
    * ``modality`` — Detected imaging modality (see :class:`Modality`).
    * ``original_filename`` — The user-supplied filename at upload time.
      Preserved for traceability; never used as a filesystem path.
    """

    crs: str | None
    transform: Any | None  # rasterio Affine
    bounds: tuple[float, float, float, float] | None
    resolution: tuple[float, float] | None
    band_count: int
    band_names: list[str] | None
    dtype: str
    nodata: float | None
    width: int
    height: int
    file_format: str
    acquisition_date: str | None
    modality: str = Modality.UNKNOWN.value
    original_filename: str | None = None


# ---------------------------------------------------------------------------
# Remote-Sensing Data Object
# ---------------------------------------------------------------------------

@dataclass
class RSDataObject:
    """Standardised internal representation of a remote-sensing product.

    This is the *model-agnostic* data container that flows through the
    preprocessing → service → model pipeline.  It binds pixel data with
    spatial metadata and lifecycle tracking.

    Design principles:

    1. **Never silently alter the user's original imagery.**  All
       transformations produce new ``RSDataObject`` instances.
    2. **Prefer references over copies** — ``source_path`` points to the
       original file on disk; the ``data`` array may be loaded lazily.
    3. **Traceability** — ``preprocessing_history`` logs every transform
       applied so that the downstream consumer knows exactly what happened.

    Fields:

    * ``data`` — Raster pixel data as ``(bands, height, width)`` array.
    * ``metadata`` — Extracted spatial/spectral metadata.
    * ``source_path`` — Absolute path to the original file on disk.
    * ``image_id`` — Stable unique identifier generated at ingestion.
    * ``original_filename`` — The user-supplied filename; never used as path.
    * ``file_format`` — ``"geotiff"``, ``"tiff"``, ``"png"``, ``"jpeg"``.
    * ``modality`` — Detected or user-specified imaging modality.
    * ``preprocessing_history`` — Ordered list of transforms applied to this
      object (e.g. ``["normalised:minmax", "tiled:256x256"]``).
    * ``warnings`` — Validation warnings attached to this object.
    * ``validation_status`` — Overall validation outcome.
    """

    data: np.ndarray  # shape: (bands, height, width)
    metadata: RSMetadata
    source_path: str | None
    image_id: str  # unique identifier
    original_filename: str | None = None
    file_format: str = "unknown"
    modality: Modality = Modality.UNKNOWN
    preprocessing_history: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    validation_status: ValidationStatus = ValidationStatus.VALID

    def add_preprocessing_step(self, description: str) -> None:
        """Record a preprocessing transform that was applied."""
        self.preprocessing_history.append(description)

    def add_warning(self, warning: str) -> None:
        """Attach a validation warning."""
        self.warnings.append(warning)


# ---------------------------------------------------------------------------
# Execution / Analysis Types (unchanged from Phase 0)
# ---------------------------------------------------------------------------

@dataclass
class ExecutionStep:
    """Represents a single step taken during execution planning/routing."""

    step_number: int
    action: str
    status: Literal["completed", "failed", "skipped"]
    duration_ms: float | None
    observable_output: str | None


@dataclass
class AnalysisResult:
    """Final comprehensive response structure."""

    answer: str
    confidence: ConfidenceScore | None
    evidence: list[Evidence]
    execution_trace: list[ExecutionStep]
    metadata: dict[str, Any]
    warnings: list[str]
    errors: list[str]
    intent: QueryIntent
