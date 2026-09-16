"""File and image validation for the SatQuery AI ingestion pipeline.

Validation produces structured results with three possible categories:

* ``VALID`` — imagery passes all checks.
* ``VALID_WITH_WARNINGS`` — imagery is usable but has non-fatal issues.
* ``INVALID`` — imagery cannot be used.

Warnings must *never* automatically make otherwise usable imagery invalid.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from backend.core.exceptions import ValidationError
from backend.core.logging import get_logger
from backend.core.types import Modality, RSDataObject, RSMetadata, ValidationStatus

logger = get_logger(__name__)

MAX_FILE_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB default
MAX_DIMENSION: int = 65_536  # pixels — warn above this
ALLOWED_EXTENSIONS: set[str] = {".tif", ".tiff", ".png", ".jpg", ".jpeg"}


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Structured output of the validation pipeline.

    Attributes:
        valid: ``True`` if the file can be used (even with warnings).
        category: Overall validation category.
        errors: Fatal issues that prevent usage.
        warnings: Non-fatal issues — file is still usable.
    """

    valid: bool
    category: ValidationStatus = ValidationStatus.VALID
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class TemporalPairValidation:
    """Compatibility report for a bi-temporal image pair.

    Attributes:
        compatible: ``True`` if the pair can be used for change detection.
        needs_alignment: ``True`` if spatial co-registration is required.
        needs_reprojection: ``True`` if CRS reprojection is required.
        overlap_percent: Estimated geographic overlap (0–100).
        issues: List of detected problems.
    """

    compatible: bool
    needs_alignment: bool
    needs_reprojection: bool
    overlap_percent: float
    issues: list[str] = field(default_factory=list)


@dataclass
class CrossModalValidation:
    """Compatibility report for an optical + SAR pair.

    Attributes:
        compatible: ``True`` if the pair can be used for cross-modal analysis.
        spatial_overlap: Estimated geographic overlap (0–100).
        resolution_ratio: Ratio of resolutions (ideally close to 1.0).
        issues: Detected problems.
    """

    compatible: bool
    spatial_overlap: float
    resolution_ratio: float
    issues: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# File-level validation
# ---------------------------------------------------------------------------

def validate_image_file(
    file_path: str,
    max_size_bytes: int = MAX_FILE_SIZE_BYTES,
) -> ValidationResult:
    """Validate an image file before ingestion.

    Checks (in order):

    1. File existence.
    2. Extension is in the supported set.
    3. File size is within limits.
    4. File is readable (not corrupt).
    5. Dimensions are reasonable.
    6. Data type is supported.
    7. CRS presence (warning if missing).
    8. Acquisition timestamp presence (warning if missing).

    Args:
        file_path: Path to the image file.
        max_size_bytes: Maximum allowed file size in bytes.

    Returns:
        A :class:`ValidationResult` with category and messages.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Existence
    if not os.path.exists(file_path):
        errors.append("File does not exist.")
        return ValidationResult(
            valid=False,
            category=ValidationStatus.INVALID,
            errors=errors,
        )

    # 2. Extension
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        errors.append(f"Unsupported file extension: {ext}")
        return ValidationResult(
            valid=False,
            category=ValidationStatus.INVALID,
            errors=errors,
        )

    # 3. Size
    file_size = os.path.getsize(file_path)
    if file_size > max_size_bytes:
        errors.append(
            f"File size ({file_size:,} bytes) exceeds limit "
            f"({max_size_bytes:,} bytes)."
        )
        return ValidationResult(
            valid=False,
            category=ValidationStatus.INVALID,
            errors=errors,
        )
    if file_size == 0:
        errors.append("File is empty (0 bytes).")
        return ValidationResult(
            valid=False,
            category=ValidationStatus.INVALID,
            errors=errors,
        )

    # 4. Readability — attempt to open with rasterio or Pillow
    is_tiff = ext in (".tif", ".tiff")
    width = height = band_count = 0
    dtype_str = "unknown"
    has_crs = False
    has_acq_date = False

    if is_tiff:
        try:
            import rasterio

            with rasterio.open(file_path) as src:
                width = src.width
                height = src.height
                band_count = src.count
                dtype_str = str(src.dtypes[0]) if src.dtypes else "unknown"
                has_crs = src.crs is not None
                tags = src.tags() or {}
                has_acq_date = any(
                    k in tags
                    for k in ("TIFFTAG_DATETIME", "acquisition_date", "datetime")
                )
        except Exception as exc:
            errors.append(f"File is corrupt or unreadable: {exc}")
            return ValidationResult(
                valid=False,
                category=ValidationStatus.INVALID,
                errors=errors,
            )
    else:
        try:
            from PIL import Image

            with Image.open(file_path) as img:
                img.load()
                width, height = img.size
                band_count = len(img.getbands())
                dtype_str = "uint8"
        except Exception as exc:
            errors.append(f"Image is corrupt or unreadable: {exc}")
            return ValidationResult(
                valid=False,
                category=ValidationStatus.INVALID,
                errors=errors,
            )

    # 5. Dimensions
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        warnings.append(
            f"Unusually large raster ({width}×{height}). "
            "Processing may be slow; tiling is recommended."
        )

    # 6. Data type — we accept all NumPy-compatible dtypes but warn on exotic ones
    unsupported_dtypes = {"complex64", "complex128"}
    if dtype_str in unsupported_dtypes:
        errors.append(f"Unsupported data type: {dtype_str}")
        return ValidationResult(
            valid=False,
            category=ValidationStatus.INVALID,
            errors=errors,
        )

    # 7. CRS
    if not has_crs:
        warnings.append("Missing CRS: file has no coordinate reference system.")

    # 8. Acquisition timestamp
    if not has_acq_date:
        warnings.append("Missing acquisition timestamp.")

    # Determine category
    if errors:
        category = ValidationStatus.INVALID
        valid = False
    elif warnings:
        category = ValidationStatus.VALID_WITH_WARNINGS
        valid = True
    else:
        category = ValidationStatus.VALID
        valid = True

    return ValidationResult(
        valid=valid,
        category=category,
        errors=errors,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Upload metadata validation
# ---------------------------------------------------------------------------

def validate_upload(
    filename: str,
    content_length: int,
    content_type: str,
    max_size_bytes: int = MAX_FILE_SIZE_BYTES,
) -> ValidationResult:
    """Validate incoming upload metadata (before saving to disk).

    Args:
        filename: Original filename from the client.
        content_length: Declared content length in bytes.
        content_type: MIME type from the request.
        max_size_bytes: Maximum allowed upload size.

    Returns:
        A :class:`ValidationResult`.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if content_length > max_size_bytes:
        errors.append("Upload exceeds maximum allowed size.")

    valid_mime_types = {"image/tiff", "image/png", "image/jpeg"}
    if content_type not in valid_mime_types:
        # Also accept application/octet-stream for GeoTIFF uploads
        if content_type != "application/octet-stream":
            errors.append(f"Invalid MIME type: {content_type}")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        errors.append(f"Unsupported file extension: {ext}")

    if errors:
        return ValidationResult(
            valid=False, category=ValidationStatus.INVALID, errors=errors
        )
    return ValidationResult(
        valid=True,
        category=ValidationStatus.VALID,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Temporal pair validation
# ---------------------------------------------------------------------------

def validate_temporal_pair(
    image_before: RSDataObject,
    image_after: RSDataObject,
) -> TemporalPairValidation:
    """Check whether two images are compatible for temporal change detection.

    Checks CRS, resolution, bounds overlap, dimensions, and acquisition
    timestamps where metadata is available.

    Args:
        image_before: The earlier image.
        image_after: The later image.

    Returns:
        A :class:`TemporalPairValidation` report.
    """
    issues: list[str] = []
    needs_reprojection = False
    needs_alignment = False

    # CRS
    crs_a = image_before.metadata.crs
    crs_b = image_after.metadata.crs
    if crs_a and crs_b:
        if crs_a != crs_b:
            needs_reprojection = True
            issues.append(f"CRS mismatch: {crs_a} vs {crs_b}. Reprojection required.")
    elif not crs_a or not crs_b:
        issues.append("One or both images lack CRS. Spatial comparison unreliable.")

    # Resolution
    res_a = image_before.metadata.resolution
    res_b = image_after.metadata.resolution
    if res_a and res_b:
        ratio = res_a[0] / res_b[0] if res_b[0] != 0 else float("inf")
        if not (0.9 <= ratio <= 1.1):
            needs_alignment = True
            issues.append(
                f"Resolution mismatch: {res_a} vs {res_b}. Resampling needed."
            )

    # Bounds overlap
    overlap = _compute_bounds_overlap(
        image_before.metadata.bounds, image_after.metadata.bounds
    )

    if overlap == 0.0 and (image_before.metadata.bounds and image_after.metadata.bounds):
        issues.append("Images have no spatial overlap.")

    # Dimensions
    shape_a = image_before.data.shape
    shape_b = image_after.data.shape
    if shape_a != shape_b:
        needs_alignment = True
        issues.append(f"Dimension mismatch: {shape_a} vs {shape_b}.")

    compatible = overlap > 0 or (
        not image_before.metadata.bounds and not image_after.metadata.bounds
    )

    return TemporalPairValidation(
        compatible=compatible and not needs_reprojection,
        needs_alignment=needs_alignment,
        needs_reprojection=needs_reprojection,
        overlap_percent=overlap,
        issues=issues,
    )


# ---------------------------------------------------------------------------
# Cross-modal validation
# ---------------------------------------------------------------------------

def validate_cross_modal_pair(
    optical: RSDataObject,
    sar: RSDataObject,
) -> CrossModalValidation:
    """Validate if optical and SAR images can be used for cross-modal analysis.

    Args:
        optical: The optical image.
        sar: The SAR image.

    Returns:
        A :class:`CrossModalValidation` report.
    """
    issues: list[str] = []

    overlap = _compute_bounds_overlap(optical.metadata.bounds, sar.metadata.bounds)

    res_optical = optical.metadata.resolution or (1.0, 1.0)
    res_sar = sar.metadata.resolution or (1.0, 1.0)
    ratio = res_optical[0] / res_sar[0] if res_sar[0] != 0 else float("inf")

    if optical.metadata.crs and sar.metadata.crs:
        if optical.metadata.crs != sar.metadata.crs:
            issues.append("CRS mismatch between optical and SAR images.")

    if overlap < 10.0 and (optical.metadata.bounds and sar.metadata.bounds):
        issues.append("Low spatial overlap between optical and SAR images.")

    compatible = len(issues) == 0

    return CrossModalValidation(
        compatible=compatible,
        spatial_overlap=overlap,
        resolution_ratio=ratio,
        issues=issues,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_bounds_overlap(
    bounds_a: tuple[float, float, float, float] | None,
    bounds_b: tuple[float, float, float, float] | None,
) -> float:
    """Compute percentage overlap of two bounding boxes.

    Bounds are in ``(left, bottom, right, top)`` format.  Returns 0–100.
    """
    if bounds_a is None or bounds_b is None:
        return 100.0  # assume full overlap when bounds unknown

    left_a, bottom_a, right_a, top_a = bounds_a
    left_b, bottom_b, right_b, top_b = bounds_b

    inter_left = max(left_a, left_b)
    inter_bottom = max(bottom_a, bottom_b)
    inter_right = min(right_a, right_b)
    inter_top = min(top_a, top_b)

    if inter_left >= inter_right or inter_bottom >= inter_top:
        return 0.0

    inter_area = (inter_right - inter_left) * (inter_top - inter_bottom)
    area_a = (right_a - left_a) * (top_a - bottom_a)

    if area_a <= 0:
        return 0.0

    return min(100.0, (inter_area / area_a) * 100.0)
