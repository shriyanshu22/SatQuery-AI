"""Image loading for remote-sensing files.

Supports GeoTIFF/TIFF (via rasterio) and conventional formats PNG/JPEG
(via Pillow) needed for benchmark/demo workflows.

Design principles:

* Detect file format from extension **and** header magic bytes.
* Safely open files; detect corrupt/unreadable rasters.
* Extract all available geospatial metadata.
* Never assume: every TIFF is RGB, every raster has CRS, every raster is
  single-band, or every multi-band image is multispectral.
* Preserve the original file — loading produces a *read-only snapshot*.
"""

from __future__ import annotations

import os
import struct
import uuid
from typing import Any

import numpy as np
from PIL import Image

from backend.core.exceptions import ImageLoadError, UnsupportedFormatError
from backend.core.logging import get_logger
from backend.core.types import Modality, RSDataObject, RSMetadata, ValidationStatus

logger = get_logger(__name__)

# Extension → canonical format name mapping
_FORMAT_MAP: dict[str, str] = {
    ".tif": "geotiff",
    ".tiff": "geotiff",
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
}

# TIFF magic bytes (little-endian II or big-endian MM)
_TIFF_MAGIC_LE = b"II"
_TIFF_MAGIC_BE = b"MM"
_PNG_MAGIC = b"\x89PNG"
_JPEG_MAGIC = b"\xff\xd8\xff"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def generate_image_id(file_path: str | None = None) -> str:
    """Generate a unique identifier for an image.

    When *file_path* is provided the ID is deterministic (UUID-5 based on the
    path).  Otherwise a random UUID-4 is returned.

    Args:
        file_path: Optional filesystem path used as the seed.

    Returns:
        A UUID string.
    """
    if file_path:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"file://{file_path}"))
    return str(uuid.uuid4())


def detect_format(file_path: str) -> str:
    """Detect the file format from extension and, where possible, magic bytes.

    Args:
        file_path: Path to the file.

    Returns:
        Canonical format string (``"geotiff"``, ``"png"``, ``"jpeg"``).

    Raises:
        UnsupportedFormatError: If the extension is not recognised.
    """
    ext = os.path.splitext(file_path)[1].lower()
    fmt = _FORMAT_MAP.get(ext)
    if fmt is None:
        raise UnsupportedFormatError(f"Unsupported file extension: {ext}")

    # Cross-check with magic bytes when the file exists
    if os.path.isfile(file_path):
        try:
            with open(file_path, "rb") as fh:
                header = fh.read(8)
            if ext in (".tif", ".tiff"):
                if not (header[:2] in (_TIFF_MAGIC_LE, _TIFF_MAGIC_BE)):
                    logger.warning(
                        "tiff_magic_mismatch",
                        file=file_path,
                        header=header[:4].hex(),
                    )
            elif ext == ".png":
                if not header.startswith(_PNG_MAGIC):
                    logger.warning("png_magic_mismatch", file=file_path)
            elif ext in (".jpg", ".jpeg"):
                if not header.startswith(_JPEG_MAGIC):
                    logger.warning("jpeg_magic_mismatch", file=file_path)
        except OSError:
            pass  # inability to read header is not fatal at format-detection stage

    return fmt


def detect_format_from_magic(file_path: str) -> str | None:
    """Attempt to detect format purely from magic bytes (no extension check).

    Returns:
        Canonical format string, or ``None`` if unrecognised.
    """
    try:
        with open(file_path, "rb") as fh:
            header = fh.read(8)
    except OSError:
        return None

    if header[:2] in (_TIFF_MAGIC_LE, _TIFF_MAGIC_BE):
        return "geotiff"
    if header[:4] == _PNG_MAGIC:
        return "png"
    if header[:3] == _JPEG_MAGIC:
        return "jpeg"
    return None


# ---------------------------------------------------------------------------
# GeoTIFF / TIFF loader (rasterio)
# ---------------------------------------------------------------------------

def load_geotiff(file_path: str, image_id: str | None = None) -> RSDataObject:
    """Load a GeoTIFF or plain TIFF using *rasterio*.

    Extracts CRS, affine transform, bounds, resolution, band count, data type,
    nodata, and all available metadata tags.  Missing CRS is handled
    gracefully: a warning is attached rather than raising an error.

    Args:
        file_path: Absolute or relative path to a ``.tif``/``.tiff`` file.

    Returns:
        A fully populated :class:`RSDataObject`.

    Raises:
        ImageLoadError: If the file cannot be opened or read.
    """
    try:
        import rasterio
    except ImportError as exc:
        raise ImageLoadError(
            "rasterio is required to load GeoTIFF files. "
            "Install it with: pip install rasterio"
        ) from exc

    try:
        with rasterio.open(file_path) as src:
            data = src.read()  # shape: (bands, height, width)

            crs_str = str(src.crs) if src.crs else None
            transform = src.transform
            bounds = tuple(src.bounds) if src.bounds else None
            resolution: tuple[float, float] | None = None
            if src.res:
                resolution = (float(src.res[0]), float(src.res[1]))

            band_names: list[str] | None = None
            descriptions = src.descriptions
            if descriptions and any(d is not None for d in descriptions):
                band_names = [d or f"band_{i+1}" for i, d in enumerate(descriptions)]

            # Attempt to extract acquisition date from tags
            tags = src.tags() or {}
            acq_date = (
                tags.get("TIFFTAG_DATETIME")
                or tags.get("acquisition_date")
                or tags.get("datetime")
            )

            warnings: list[str] = []
            if crs_str is None:
                warnings.append("Missing CRS: file has no coordinate reference system.")
            if acq_date is None:
                warnings.append("Missing acquisition timestamp.")

            metadata = RSMetadata(
                crs=crs_str,
                transform=transform,
                bounds=bounds,
                resolution=resolution,
                band_count=src.count,
                band_names=band_names,
                dtype=str(src.dtypes[0]) if src.dtypes else "unknown",
                nodata=float(src.nodata) if src.nodata is not None else None,
                width=src.width,
                height=src.height,
                file_format="geotiff",
                acquisition_date=acq_date,
                original_filename=os.path.basename(file_path),
            )

            image_id_val = image_id or generate_image_id(file_path)

            return RSDataObject(
                data=data,
                metadata=metadata,
                source_path=os.path.abspath(file_path),
                image_id=image_id_val,
                original_filename=os.path.basename(file_path),
                file_format="geotiff",
                modality=Modality.UNKNOWN,  # determined later by modality detector
                warnings=warnings,
                validation_status=(
                    ValidationStatus.VALID_WITH_WARNINGS
                    if warnings
                    else ValidationStatus.VALID
                ),
            )
    except Exception as exc:
        if isinstance(exc, ImageLoadError):
            raise
        raise ImageLoadError(
            f"Failed to load GeoTIFF: {file_path}",
            details={"file": file_path},
            original_exception=exc,
        ) from exc


# ---------------------------------------------------------------------------
# Standard image loader (Pillow)
# ---------------------------------------------------------------------------

def load_standard_image(file_path: str, image_id: str | None = None) -> RSDataObject:
    """Load a conventional image (PNG, JPEG) using *Pillow*.

    The resulting data array is reshaped to ``(bands, height, width)`` for
    consistency with the rasterio convention.  No geospatial metadata is
    available for these formats.

    Args:
        file_path: Path to a PNG or JPEG file.

    Returns:
        An :class:`RSDataObject` with CRS/transform set to ``None``.

    Raises:
        ImageLoadError: If the file cannot be opened or decoded.
    """
    try:
        img = Image.open(file_path)
        img.load()  # force full decode — catches truncated files

        arr = np.asarray(img)

        # Convert (H, W, C) → (C, H, W); handle grayscale (H, W)
        if arr.ndim == 3:
            data = np.transpose(arr, (2, 0, 1))  # (C, H, W)
        elif arr.ndim == 2:
            data = arr[np.newaxis, :, :]  # (1, H, W)
        else:
            raise ImageLoadError(f"Unexpected image shape: {arr.shape}")

        fmt = detect_format(file_path)
        band_count = data.shape[0]
        band_names = None
        if band_count == 1:
            band_names = ["gray"]
        elif band_count == 3:
            band_names = ["R", "G", "B"]
        elif band_count == 4:
            band_names = ["R", "G", "B", "A"]

        warnings: list[str] = [
            "No geospatial metadata: file is a conventional image (PNG/JPEG).",
            "Missing CRS: file has no coordinate reference system.",
            "Missing acquisition timestamp.",
        ]

        metadata = RSMetadata(
            crs=None,
            transform=None,
            bounds=None,
            resolution=None,
            band_count=band_count,
            band_names=band_names,
            dtype=str(data.dtype),
            nodata=None,
            width=data.shape[2],
            height=data.shape[1],
            file_format=fmt,
            acquisition_date=None,
            original_filename=os.path.basename(file_path),
        )

        image_id_val = image_id or generate_image_id(file_path)

        return RSDataObject(
            data=data,
            metadata=metadata,
            source_path=os.path.abspath(file_path),
            image_id=image_id_val,
            original_filename=os.path.basename(file_path),
            file_format=fmt,
            modality=Modality.UNKNOWN,
            warnings=warnings,
            validation_status=ValidationStatus.VALID_WITH_WARNINGS,
        )
    except Exception as exc:
        if isinstance(exc, ImageLoadError):
            raise
        raise ImageLoadError(
            f"Failed to load image: {file_path}",
            details={"file": file_path},
            original_exception=exc,
        ) from exc


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

def load_image(file_path: str, image_id: str | None = None) -> RSDataObject:
    """Load a remote-sensing or conventional image file.

    Detects the format and dispatches to the appropriate loader:

    * ``.tif`` / ``.tiff`` → :func:`load_geotiff`
    * ``.png`` / ``.jpg`` / ``.jpeg`` → :func:`load_standard_image`

    Args:
        file_path: Absolute or relative path to the image file.

    Returns:
        A populated :class:`RSDataObject`.

    Raises:
        ImageLoadError: If the file does not exist or cannot be read.
        UnsupportedFormatError: If the extension is not recognised.
    """
    if not os.path.exists(file_path):
        raise ImageLoadError(f"File not found: {file_path}")

    fmt = detect_format(file_path)
    if fmt == "geotiff":
        return load_geotiff(file_path, image_id=image_id)
    return load_standard_image(file_path, image_id=image_id)
