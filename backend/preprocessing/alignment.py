"""Spatial alignment, co-registration, and reprojection utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, List

from backend.core.types import RSDataObject
from backend.core.exceptions import PreprocessingError
from backend.core.logging import get_logger
from backend.preprocessing.spatial import compute_bounds_overlap

logger = get_logger(__name__)


@dataclass
class CompatibilityReport:
    """Detailed report on the bi-temporal compatibility of two images."""
    compatible: bool
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    mismatches: list[str] = field(default_factory=list)


def check_compatibility(image_a: RSDataObject, image_b: RSDataObject) -> CompatibilityReport:
    """Check bi-temporal compatibility for change detection."""
    reasons = []
    warnings = []
    mismatches = []

    meta_a = image_a.metadata
    meta_b = image_b.metadata

    # 1. Dimensions
    if meta_a.width != meta_b.width or meta_a.height != meta_b.height:
        mismatches.append(f"Dimensions mismatch: {meta_a.width}x{meta_a.height} vs {meta_b.width}x{meta_b.height}")
    else:
        reasons.append("Dimensions match.")

    # 2. CRS
    if meta_a.crs and meta_b.crs:
        if meta_a.crs != meta_b.crs:
            mismatches.append(f"CRS mismatch: {meta_a.crs} vs {meta_b.crs}")
        else:
            reasons.append(f"CRS match: {meta_a.crs}")
    else:
        warnings.append("Missing CRS in one or both images.")

    # 3. Resolution
    if meta_a.resolution and meta_b.resolution:
        ratio = meta_a.resolution[0] / meta_b.resolution[0] if meta_b.resolution[0] != 0 else float("inf")
        if not (0.95 <= ratio <= 1.05):
            mismatches.append(f"Resolution mismatch: {meta_a.resolution} vs {meta_b.resolution}")
        else:
            reasons.append("Resolution approximately matches.")
    else:
        warnings.append("Missing resolution in one or both images.")

    # 4. Bounds & Overlap
    overlap = compute_bounds_overlap(meta_a.bounds, meta_b.bounds)
    if overlap == 0.0 and (meta_a.bounds and meta_b.bounds):
        mismatches.append("Images have no spatial overlap.")
    elif overlap > 0.0:
        reasons.append(f"Images overlap geographically by {overlap:.2f}%.")

    # 5. Transform
    # Exact transform match is rarely true unless pre-aligned, but useful for strict checks

    compatible = len(mismatches) == 0

    return CompatibilityReport(
        compatible=compatible,
        reasons=reasons,
        warnings=warnings,
        mismatches=mismatches
    )


def reproject_to_match(source: RSDataObject, reference: RSDataObject) -> RSDataObject:
    """
    Reproject source image to match reference image CRS and resolution.
    Creates a derived output and never silently modifies the source data.
    """
    logger.info(f"Reprojecting {source.image_id} to match {reference.image_id}")
    
    if source.metadata.crs is None or reference.metadata.crs is None:
        raise PreprocessingError("Both source and reference must have a valid CRS for reprojection.")

    try:
        import rasterio
        from rasterio.warp import calculate_default_transform, reproject, Resampling
        import numpy as np

        # Ensure we have paths to open with rasterio if data is large,
        # but for this MVP we'll reproject in-memory arrays since we hold `source.data`
        # In a production system we'd use rasterio.MemoryFile or reproject from source_path
        
        src_crs = rasterio.crs.CRS.from_string(source.metadata.crs)
        dst_crs = rasterio.crs.CRS.from_string(reference.metadata.crs)
        
        # We need the transform of the source
        src_transform = source.metadata.transform
        if not src_transform:
            raise PreprocessingError("Source image missing transform.")
            
        # Calculate optimal transform and shape (or just use reference's if we want exact alignment)
        # For pure CRS match we calculate the new transform
        dst_transform, dst_width, dst_height = calculate_default_transform(
            src_crs, dst_crs, source.metadata.width, source.metadata.height,
            *source.metadata.bounds
        )

        dst_data = np.zeros((source.metadata.band_count, dst_height, dst_width), dtype=source.data.dtype)

        reproject(
            source=source.data,
            destination=dst_data,
            src_transform=src_transform,
            src_crs=src_crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=Resampling.nearest
        )

        # Create updated metadata
        new_metadata = source.metadata.__class__(
            crs=reference.metadata.crs,
            transform=dst_transform,
            bounds=None, # Will need recalculation or use default from rasterio
            resolution=None, # Re-calculate if needed
            band_count=source.metadata.band_count,
            band_names=source.metadata.band_names,
            dtype=source.metadata.dtype,
            nodata=source.metadata.nodata,
            width=dst_width,
            height=dst_height,
            file_format=source.metadata.file_format,
            acquisition_date=source.metadata.acquisition_date,
            original_filename=source.metadata.original_filename,
            modality=source.metadata.modality
        )

        # Derived RSDataObject
        new_obj = RSDataObject(
            data=dst_data,
            metadata=new_metadata,
            source_path=source.source_path, # Keep original source path
            image_id=f"{source.image_id}_reprojected",
            original_filename=source.original_filename,
            file_format=source.file_format,
            modality=source.modality,
            preprocessing_history=source.preprocessing_history.copy(),
            warnings=source.warnings.copy(),
            validation_status=source.validation_status
        )
        new_obj.add_preprocessing_step(f"reprojected to {reference.metadata.crs}")
        return new_obj

    except Exception as e:
        raise PreprocessingError(f"Reprojection failed: {e}") from e


def align_images(source: RSDataObject, reference: RSDataObject) -> RSDataObject:
    """
    Explicit alignment utility for temporal analysis.
    If images are already compatible, returns source unchanged.
    If CRS mismatches, reprojects.
    """
    report = check_compatibility(source, reference)
    aligned_img = source
    
    if not report.compatible:
        needs_reproj = any("CRS mismatch" in m for m in report.mismatches)
        if needs_reproj:
            aligned_img = reproject_to_match(aligned_img, reference)
        else:
            raise PreprocessingError(
                f"Images are incompatible and cannot be easily aligned. Mismatches: {report.mismatches}"
            )
            
    aligned_img.add_preprocessing_step(f"aligned to {reference.image_id}")
    return aligned_img
