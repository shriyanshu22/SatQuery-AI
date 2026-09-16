"""Spatial metadata extraction and compatibility utilities."""

from __future__ import annotations

from typing import Any
from backend.core.types import RSMetadata
from backend.core.logging import get_logger

logger = get_logger(__name__)


def extract_spatial_metadata(file_path: str) -> dict[str, Any]:
    """Extract spatial metadata from a file using rasterio.
    
    This is useful for standalone extraction when not loading the full image.
    """
    try:
        import rasterio
        with rasterio.open(file_path) as src:
            return {
                "crs": str(src.crs) if src.crs else None,
                "transform": src.transform,
                "bounds": tuple(src.bounds) if src.bounds else None,
                "resolution": (float(src.res[0]), float(src.res[1])) if src.res else None,
                "width": src.width,
                "height": src.height,
            }
    except Exception as e:
        logger.warning(f"Could not extract spatial metadata from {file_path}: {e}")
        return {
            "crs": None,
            "transform": None,
            "bounds": None,
            "resolution": None,
            "width": 0,
            "height": 0,
        }


def compute_bounds_overlap(
    bounds_a: tuple[float, float, float, float] | None,
    bounds_b: tuple[float, float, float, float] | None,
) -> float:
    """Compute percentage overlap of two bounding boxes.
    
    Bounds are in ``(left, bottom, right, top)`` format. Returns 0-100.
    """
    if bounds_a is None or bounds_b is None:
        return 100.0  # Assumed full overlap if bounds are unknown

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


def are_spatially_compatible(meta_a: RSMetadata, meta_b: RSMetadata) -> tuple[bool, list[str]]:
    """Determine if two metadata objects indicate spatial compatibility."""
    issues = []
    if meta_a.crs and meta_b.crs and meta_a.crs != meta_b.crs:
        issues.append(f"CRS mismatch: {meta_a.crs} vs {meta_b.crs}")
        
    overlap = compute_bounds_overlap(meta_a.bounds, meta_b.bounds)
    if overlap == 0.0 and (meta_a.bounds and meta_b.bounds):
        issues.append("No spatial overlap.")
        
    res_a = meta_a.resolution
    res_b = meta_b.resolution
    if res_a and res_b:
        ratio = res_a[0] / res_b[0] if res_b[0] != 0 else float("inf")
        if not (0.9 <= ratio <= 1.1):
            issues.append(f"Resolution mismatch: {res_a} vs {res_b}")
            
    compatible = len(issues) == 0
    return compatible, issues


def reproject_bounds(bounds: tuple[float, float, float, float], src_crs: str, dst_crs: str) -> tuple[float, float, float, float] | None:
    """Reproject bounds from one CRS to another."""
    try:
        import rasterio.warp
        from rasterio.crs import CRS
        
        src = CRS.from_string(src_crs)
        dst = CRS.from_string(dst_crs)
        
        left, bottom, right, top = bounds
        new_bounds = rasterio.warp.transform_bounds(src, dst, left, bottom, right, top)
        return tuple(new_bounds)
    except Exception as e:
        logger.error(f"Failed to reproject bounds from {src_crs} to {dst_crs}: {e}")
        return None
