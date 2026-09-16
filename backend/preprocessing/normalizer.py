from __future__ import annotations

from typing import List, Literal
import numpy as np

from backend.core.types import RSDataObject
from backend.core.logging import get_logger

logger = get_logger(__name__)


def normalize_image(data: np.ndarray, method: Literal['minmax', 'zscore', 'percentile'] = 'minmax') -> np.ndarray:
    """
    Normalize image data based on the chosen method.
    """
    data = data.astype(np.float32)
    
    if method == 'minmax':
        d_min, d_max = data.min(), data.max()
        if d_max - d_min == 0:
            return data
        return (data - d_min) / (d_max - d_min)
        
    elif method == 'zscore':
        mean, std = data.mean(), data.std()
        if std == 0:
            return data
        return (data - mean) / std
        
    elif method == 'percentile':
        p2, p98 = np.percentile(data, (2, 98))
        if p98 - p2 == 0:
            return data
        clipped = np.clip(data, p2, p98)
        return (clipped - p2) / (p98 - p2)
        
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def select_bands(rs_data: RSDataObject, band_indices: List[int]) -> RSDataObject:
    """
    Select specific bands from a multi-band image and return a new RSDataObject.
    """
    if len(rs_data.data.shape) != 3:
        raise ValueError("Image data must be 3-dimensional (bands, height, width).")
        
    new_data = rs_data.data[band_indices, :, :]
    new_band_names = [rs_data.metadata.band_names[i] for i in band_indices] if rs_data.metadata.band_names else []
    
    # Create a shallow copy of metadata with updated band names
    new_metadata = rs_data.metadata.__class__(
        crs=rs_data.metadata.crs,
        transform=rs_data.metadata.transform,
        bounds=rs_data.metadata.bounds,
        resolution=rs_data.metadata.resolution,
        band_count=len(band_indices),
        band_names=new_band_names,
        dtype=rs_data.metadata.dtype,
        nodata=rs_data.metadata.nodata,
        width=rs_data.metadata.width,
        height=rs_data.metadata.height,
        file_format=rs_data.metadata.file_format,
        acquisition_date=rs_data.metadata.acquisition_date,
        original_filename=rs_data.metadata.original_filename,
        modality=rs_data.metadata.modality
    )
    
    new_obj = RSDataObject(
        data=new_data,
        metadata=new_metadata,
        source_path=rs_data.source_path,
        image_id=f"{rs_data.image_id}_bands_{'_'.join(map(str, band_indices))}",
        original_filename=rs_data.original_filename,
        file_format=rs_data.file_format,
        modality=rs_data.modality,
        preprocessing_history=rs_data.preprocessing_history.copy(),
        warnings=rs_data.warnings.copy(),
        validation_status=rs_data.validation_status
    )
    new_obj.add_preprocessing_step(f"select_bands: {band_indices}")
    return new_obj


def compose_rgb(rs_data: RSDataObject, red_band: int, green_band: int, blue_band: int) -> RSDataObject:
    """
    Create an RGB composite from a multi-band image.
    Expects data in (bands, height, width) format. Returns a derived RSDataObject.
    """
    selected = select_bands(rs_data, [red_band, green_band, blue_band])
    selected.add_preprocessing_step(f"compose_rgb: {red_band}, {green_band}, {blue_band}")
    return selected


def to_uint8(data: np.ndarray) -> np.ndarray:
    """
    Convert image data to uint8 format. Assumes data is already normalized to [0, 1] if float.
    """
    if data.dtype == np.uint8:
        return data
        
    if np.issubdtype(data.dtype, np.floating):
        return np.clip(data * 255.0, 0, 255).astype(np.uint8)
        
    # Scale integer max ranges to 255
    d_max = data.max()
    if d_max > 0:
        return ((data / d_max) * 255).astype(np.uint8)
        
    return data.astype(np.uint8)
