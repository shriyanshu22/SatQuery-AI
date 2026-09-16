"""
Preprocessing module for SatQuery AI.
Handles image loading, validation, normalization, tiling, alignment, and format adaptations.
"""

from __future__ import annotations

from backend.preprocessing.image_loader import load_image
from backend.preprocessing.validators import validate_image_file, validate_upload
from backend.preprocessing.modality import detect_modality
from backend.preprocessing.preview import generate_preview
from backend.preprocessing.spatial import extract_spatial_metadata, are_spatially_compatible
from backend.preprocessing.alignment import align_images, check_compatibility
from backend.preprocessing.tiling import tile_image, tile_from_file, reassemble_tiles
from backend.preprocessing.normalizer import normalize_image, select_bands, compose_rgb

__all__ = [
    "load_image",
    "validate_image_file",
    "validate_upload",
    "detect_modality",
    "generate_preview",
    "extract_spatial_metadata",
    "are_spatially_compatible",
    "align_images",
    "check_compatibility",
    "tile_image",
    "tile_from_file",
    "reassemble_tiles",
    "normalize_image",
    "select_bands",
    "compose_rgb",
]
