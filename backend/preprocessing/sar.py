"""SAR-specific preprocessing utilities.

Basic scientific preprocessing operations for Synthetic Aperture Radar data.
Differentiates between visualization preprocessing (for API preview) and
scientific preprocessing (for model inputs).

Limitations:
- Full radiometric calibration requires explicit sensor metadata (LUTs) which
  is often unavailable in generic GeoTIFFs. We provide basic scaling and filtering.
"""

from __future__ import annotations

import numpy as np

from backend.core.types import RSDataObject
from backend.core.logging import get_logger
from backend.preprocessing.modality import detect_modality

logger = get_logger(__name__)


def detect_sar_image(rs_data: RSDataObject) -> bool:
    """
    Alias for backwards compatibility if needed, but detection now happens in modality.py.
    """
    return rs_data.modality.value == "sar"


def apply_log_scaling(data: np.ndarray) -> np.ndarray:
    """
    Convert linear SAR intensity to dB scale.
    Formula: 10 * log10(data)
    """
    # Prevent log(0) and negative values
    safe_data = np.clip(data, 1e-10, None)
    return 10.0 * np.log10(safe_data)


def apply_speckle_filter(data: np.ndarray, method: str = 'lee', window_size: int = 5) -> np.ndarray:
    """
    Apply a speckle filter to SAR data.
    Implements a basic box filter or uses scipy.ndimage for Lee filter approximation.
    """
    if method == 'lee':
        logger.debug(f"Applying Lee speckle filter with window size {window_size}")
        try:
            from scipy.ndimage import uniform_filter
            # A simplified Lee filter approximation for demonstration
            # In a true scientific pipeline, a more robust implementation is needed.
            mean = uniform_filter(data, size=window_size)
            sqr_mean = uniform_filter(data**2, size=window_size)
            var = sqr_mean - mean**2
            # Assuming noise variance is related to the overall image variance
            noise_var = data.var()
            
            # Prevent division by zero
            weights = np.maximum(0, var - noise_var) / (var + 1e-10)
            filtered = mean + weights * (data - mean)
            return filtered
        except ImportError:
            logger.warning("scipy not installed. Skipping speckle filter.")
            return data
    else:
        logger.warning(f"Unsupported speckle filter: {method}. Returning unfiltered data.")
        return data


def calibrate_sar(data: np.ndarray, calibration_lut: np.ndarray | None = None) -> np.ndarray:
    """
    Basic radiometric calibration for SAR data.
    """
    if calibration_lut is not None:
        return data * calibration_lut
    return data


def preprocess_sar(rs_data: RSDataObject) -> RSDataObject:
    """
    Standard preprocessing pipeline for SAR images for scientific model input.
    """
    logger.info(f"Preprocessing SAR image: {rs_data.image_id}")
    
    processed_data = rs_data.data.copy()
    
    # 1. Calibration (mock)
    processed_data = calibrate_sar(processed_data)
    
    # 2. Speckle Filtering
    processed_data = apply_speckle_filter(processed_data, method='lee')
    
    # 3. Log Scaling (to dB)
    processed_data = apply_log_scaling(processed_data)
    
    new_metadata = rs_data.metadata.__class__(
        crs=rs_data.metadata.crs,
        transform=rs_data.metadata.transform,
        bounds=rs_data.metadata.bounds,
        resolution=rs_data.metadata.resolution,
        band_count=rs_data.metadata.band_count,
        band_names=rs_data.metadata.band_names,
        dtype=str(processed_data.dtype),
        nodata=rs_data.metadata.nodata,
        width=rs_data.metadata.width,
        height=rs_data.metadata.height,
        file_format=rs_data.metadata.file_format,
        acquisition_date=rs_data.metadata.acquisition_date,
        original_filename=rs_data.metadata.original_filename,
        modality=rs_data.metadata.modality
    )
    
    # Create new object
    new_obj = RSDataObject(
        data=processed_data,
        metadata=new_metadata,
        source_path=rs_data.source_path,
        image_id=f"{rs_data.image_id}_sar_preprocessed",
        original_filename=rs_data.original_filename,
        file_format=rs_data.file_format,
        modality=rs_data.modality,
        preprocessing_history=rs_data.preprocessing_history.copy(),
        warnings=rs_data.warnings.copy(),
        validation_status=rs_data.validation_status
    )
    new_obj.add_preprocessing_step("sar_preprocessing (calibrate, lee_filter, log_scale)")
    return new_obj
