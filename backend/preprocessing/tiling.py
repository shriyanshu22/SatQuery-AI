"""Memory-safe tiling for large remote-sensing rasters.

Provides both in-memory array tiling and windowed reading directly from
the source file (to avoid loading multi-GB images entirely).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple, Any

import numpy as np

from backend.core.types import RSDataObject
from backend.core.logging import get_logger
from backend.core.exceptions import PreprocessingError

logger = get_logger(__name__)


@dataclass
class Tile:
    """Represents a spatial tile extracted from a larger image."""
    data: np.ndarray
    row: int
    col: int
    position: Tuple[int, int]  # (x, y) starting coordinates in pixels
    size: Tuple[int, int]      # (width, height)
    source_image_id: str
    geo_bounds: tuple[float, float, float, float] | None = None


def should_tile(rs_data: RSDataObject, max_size: int = 1024) -> bool:
    """Determine whether an image should be tiled based on dimensions."""
    shape = rs_data.data.shape
    height, width = (shape[1], shape[2]) if len(shape) == 3 else (shape[0], shape[1])
    return height > max_size or width > max_size


def tile_image(rs_data: RSDataObject, tile_size: int = 256, overlap: int = 0) -> List[Tile]:
    """
    Split an in-memory image into smaller tiles.
    """
    data = rs_data.data
    shape = data.shape
    is_multiband = len(shape) == 3
    
    height = shape[1] if is_multiband else shape[0]
    width = shape[2] if is_multiband else shape[1]
    
    stride = tile_size - overlap
    if stride <= 0:
        raise ValueError("Overlap must be less than tile size.")
        
    tiles = []
    row_idx = 0
    for y in range(0, height, stride):
        col_idx = 0
        for x in range(0, width, stride):
            y_end = min(y + tile_size, height)
            x_end = min(x + tile_size, width)
            
            if is_multiband:
                tile_data = data[:, y:y_end, x:x_end]
            else:
                tile_data = data[y:y_end, x:x_end]
                
            # Geo_bounds would require calculating from transform. Left as None for in-memory simple tiling.
            tiles.append(Tile(
                data=tile_data,
                row=row_idx,
                col=col_idx,
                position=(x, y),
                size=(x_end - x, y_end - y),
                source_image_id=rs_data.image_id
            ))
            col_idx += 1
        row_idx += 1
        
    return tiles


def tile_from_file(file_path: str, image_id: str, tile_size: int = 256, overlap: int = 0) -> List[Tile]:
    """
    Extract tiles directly from a file using windowed reading.
    Extremely memory efficient for large GeoTIFFs.
    """
    try:
        import rasterio
        from rasterio.windows import Window
    except ImportError as e:
        raise PreprocessingError("rasterio is required for windowed reading.") from e
        
    stride = tile_size - overlap
    if stride <= 0:
        raise ValueError("Overlap must be less than tile size.")

    tiles = []
    try:
        with rasterio.open(file_path) as src:
            width = src.width
            height = src.height
            transform = src.transform
            
            row_idx = 0
            for y in range(0, height, stride):
                col_idx = 0
                for x in range(0, width, stride):
                    w = min(tile_size, width - x)
                    h = min(tile_size, height - y)
                    window = Window(x, y, w, h)
                    
                    data = src.read(window=window)
                    
                    # Calculate geo_bounds for this window
                    win_transform = rasterio.windows.transform(window, transform)
                    left = win_transform.c
                    top = win_transform.f
                    right = left + w * win_transform.a
                    bottom = top + h * win_transform.e
                    geo_bounds = (min(left, right), min(bottom, top), max(left, right), max(bottom, top))

                    tiles.append(Tile(
                        data=data,
                        row=row_idx,
                        col=col_idx,
                        position=(x, y),
                        size=(w, h),
                        source_image_id=image_id,
                        geo_bounds=geo_bounds
                    ))
                    col_idx += 1
                row_idx += 1
    except Exception as e:
        logger.error(f"Failed windowed tiling of {file_path}: {e}")
        raise PreprocessingError(f"Tiling failed: {e}") from e

    return tiles


def reassemble_tiles(tiles: List[Tile], original_shape: Tuple) -> np.ndarray:
    """
    Reassemble tiles back into a full image. Handles overlapping by averaging.
    """
    if not tiles:
        return np.zeros(original_shape, dtype=np.uint8)
        
    output = np.zeros(original_shape, dtype=np.float32)
    weights = np.zeros(original_shape, dtype=np.float32)
    
    is_multiband = len(original_shape) == 3
    
    for tile in tiles:
        x, y = tile.position
        w, h = tile.size
        
        if is_multiband:
            output[:, y:y+h, x:x+w] += tile.data
            weights[:, y:y+h, x:x+w] += 1.0
        else:
            output[y:y+h, x:x+w] += tile.data
            weights[y:y+h, x:x+w] += 1.0
            
    # Avoid division by zero
    weights[weights == 0] = 1.0
    return (output / weights).astype(tiles[0].data.dtype)
