"""Typed evidence dataclasses for SatQuery AI.

Provides a unified representation of evidence returned by different models.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Literal, Union

import numpy as np


@dataclass
class BoundingBox:
    """Represents a bounding box in an image."""
    x: float
    y: float
    w: float
    h: float
    label: str
    confidence: float


@dataclass
class ChangedRegion:
    """Represents a discrete region of change."""
    centroid: tuple[float, float]
    area: float
    bbox: tuple[float, float, float, float]


@dataclass
class BoundingBoxEvidence:
    """Evidence containing bounding boxes."""
    boxes: list[BoundingBox]
    source_image_id: str
    model_source: str
    type: Literal["bounding_box"] = "bounding_box"


@dataclass
class SegmentationMaskEvidence:
    """Evidence containing a segmentation mask."""
    mask_path: str | None
    mask_data: np.ndarray | None
    class_map: dict[int, str]
    source_image_id: str
    model_source: str
    type: Literal["segmentation_mask"] = "segmentation_mask"


@dataclass
class ChangeMapEvidence:
    """Evidence containing a bi-temporal change map."""
    source: str
    confidence: float
    mask_data: np.ndarray | None
    regions: list[ChangedRegion]
    type: Literal["change_map"] = "change_map"


@dataclass
class ImageCropEvidence:
    """Evidence containing a cropped region of interest."""
    crop_path: str
    region: BoundingBox
    source_image_id: str
    description: str
    type: Literal["image_crop"] = "image_crop"


@dataclass
class NumericalEvidence:
    """Evidence representing calculated metrics."""
    metric_name: str
    value: float
    unit: str | None
    description: str
    type: Literal["numerical"] = "numerical"


@dataclass
class CrossModalAgreementEvidence:
    """Evidence representing agreement between different modalities (e.g., Optical vs SAR)."""
    source: str
    confidence: float
    agreement_level: str
    supporting_optical: list[str]
    supporting_sar: list[str]
    conflict_details: str | None
    type: Literal["cross_modal_agreement"] = "cross_modal_agreement"


@dataclass
class MetadataEvidence:
    """Evidence derived from metadata rather than pixels."""
    source_file: str
    crs: str | None
    resolution: tuple[float, float] | None
    bounds: tuple[float, float, float, float] | None
    band_count: int | None
    acquisition_date: str | None
    type: Literal["metadata"] = "metadata"


Evidence = Union[
    BoundingBoxEvidence,
    SegmentationMaskEvidence,
    ChangeMapEvidence,
    ImageCropEvidence,
    NumericalEvidence,
    CrossModalAgreementEvidence,
    MetadataEvidence
]


def serialize_evidence(evidence: Evidence) -> dict[str, Any]:
    """Serialize an evidence object to a JSON-safe dictionary.
    
    Args:
        evidence: The evidence object to serialize.
        
    Returns:
        A dictionary representation of the evidence.
    """
    if not is_dataclass(evidence):
        raise TypeError("Expected a dataclass instance.")
        
    data = asdict(evidence)
    
    # Clean up non-serializable fields (like raw numpy arrays)
    if "mask_data" in data:
        del data["mask_data"]
        
    return data
