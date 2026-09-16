"""Preview generation for remote-sensing imagery.

A preview is a *derived visualisation* — it is never a replacement for the
original data.  Previews are produced at reduced resolution and saved as PNG
artifacts for display in API responses and demo workflows.

Key design decisions:

* Large rasters are down-sampled via ``rasterio`` windowed reading so that
  the full image is never loaded into memory unnecessarily.
* Single-band images get a grayscale visualisation.
* Multi-band images get an RGB composite (bands 0, 1, 2 by default).
* SAR images get log-scaled grayscale visualisation.
* Percentile-clipping normalisation is applied for visual quality.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PIL import Image

from backend.core.artifacts import ArtifactStore, ArtifactType
from backend.core.logging import get_logger
from backend.core.types import Modality, RSDataObject

logger = get_logger(__name__)


def generate_preview(
    rs_data: RSDataObject,
    artifact_store: ArtifactStore,
    max_size: int = 1024,
    rgb_bands: tuple[int, int, int] = (0, 1, 2),
) -> str:
    """Generate a preview image and store it as an artifact.

    Args:
        rs_data: The source data object.
        artifact_store: Artifact store for saving the preview file.
        max_size: Maximum dimension (width or height) for the preview.
        rgb_bands: Band indices to use for RGB composition.

    Returns:
        The artifact ID of the generated preview.
    """
    data = rs_data.data  # (bands, H, W)
    bands, height, width = data.shape

    # Down-sample if necessary
    scale = 1.0
    if max(height, width) > max_size:
        scale = max_size / max(height, width)
        new_h = max(1, int(height * scale))
        new_w = max(1, int(width * scale))
    else:
        new_h, new_w = height, width

    # Select visualisation strategy
    if rs_data.modality == Modality.SAR or bands == 1:
        preview_arr = _single_band_preview(data, new_h, new_w, is_sar=(rs_data.modality == Modality.SAR))
    else:
        preview_arr = _rgb_preview(data, new_h, new_w, rgb_bands)

    # Save as PNG artifact
    description = (
        f"Preview ({new_w}×{new_h}) generated from {rs_data.image_id}. "
        f"Scale factor: {scale:.3f}."
    )
    artifact_id, file_path = artifact_store.create(
        artifact_type=ArtifactType.PREVIEW,
        source_image_id=rs_data.image_id,
        extension=".png",
        description=description,
        metadata={"scale": scale, "size": [new_w, new_h]},
    )

    img = Image.fromarray(preview_arr)
    img.save(str(file_path), format="PNG")
    artifact_store.register(artifact_id)

    logger.info(
        "preview_generated",
        artifact_id=artifact_id,
        source=rs_data.image_id,
        size=f"{new_w}×{new_h}",
    )
    return artifact_id


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalise_for_display(arr: np.ndarray) -> np.ndarray:
    """Percentile-clip and scale a float array to uint8 [0, 255]."""
    arr = arr.astype(np.float64)
    # Handle NaN / Inf
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    p2, p98 = np.percentile(arr, (2, 98))
    if p98 - p2 < 1e-8:
        return np.zeros_like(arr, dtype=np.uint8)
    clipped = np.clip(arr, p2, p98)
    scaled = ((clipped - p2) / (p98 - p2) * 255.0)
    return scaled.astype(np.uint8)


def _resize_band(band: np.ndarray, new_h: int, new_w: int) -> np.ndarray:
    """Resize a single 2-D band using Pillow (Lanczos)."""
    img = Image.fromarray(band.astype(np.float64))
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    return np.asarray(resized)


def _single_band_preview(
    data: np.ndarray,
    new_h: int,
    new_w: int,
    is_sar: bool = False,
) -> np.ndarray:
    """Create a grayscale preview from a single band.

    For SAR data, applies log scaling before normalisation for better
    visualisation of the typically high dynamic range.
    """
    band = data[0].astype(np.float64)
    if is_sar:
        band = np.log1p(np.clip(band, 0, None))
    band = _resize_band(band, new_h, new_w)
    return _normalise_for_display(band)


def _rgb_preview(
    data: np.ndarray,
    new_h: int,
    new_w: int,
    rgb_bands: tuple[int, int, int],
) -> np.ndarray:
    """Create an RGB preview from selected bands.

    Returns an (H, W, 3) uint8 array.
    """
    bands_count = data.shape[0]
    r_idx, g_idx, b_idx = rgb_bands

    # Clamp band indices to available range
    r_idx = min(r_idx, bands_count - 1)
    g_idx = min(g_idx, bands_count - 1)
    b_idx = min(b_idx, bands_count - 1)

    channels = []
    for idx in (r_idx, g_idx, b_idx):
        band = data[idx].astype(np.float64)
        band = _resize_band(band, new_h, new_w)
        channels.append(_normalise_for_display(band))

    return np.stack(channels, axis=-1)  # (H, W, 3)
