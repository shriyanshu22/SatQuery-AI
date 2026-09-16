"""Pytest fixtures for SatQuery AI tests."""

from __future__ import annotations

import pytest
import pytest_asyncio
import numpy as np
from httpx import AsyncClient, ASGITransport

from backend.core.types import RSDataObject, RSMetadata
from backend.core.config import Settings
from backend.api.main import create_app


@pytest.fixture
def sample_rgb_image() -> np.ndarray:
    """Create a sample 3-band RGB image (256x256)."""
    return np.random.randint(0, 255, (3, 256, 256), dtype=np.uint8)


@pytest.fixture
def sample_rs_metadata() -> RSMetadata:
    """Create sample remote sensing metadata."""
    return RSMetadata(
        crs="EPSG:32633",
        transform=None,
        bounds=(0.0, 0.0, 100.0, 100.0),
        resolution=(10.0, 10.0),
        band_count=3,
        band_names=["B02", "B03", "B04"],
        dtype="uint8",
        nodata=None,
        width=256,
        height=256,
        file_format="GeoTIFF",
        acquisition_date="2023-10-01T10:00:00Z",
    )


@pytest.fixture
def sample_rs_data_object(
    sample_rgb_image: np.ndarray, sample_rs_metadata: RSMetadata
) -> RSDataObject:
    """Create a sample RSDataObject."""
    return RSDataObject(
        data=sample_rgb_image,
        metadata=sample_rs_metadata,
        source_path=None,
        image_id="test_img_01",
    )


@pytest.fixture
def sample_multispectral_image() -> np.ndarray:
    """Create a sample 12-band multispectral image."""
    return np.random.randint(0, 10000, (12, 120, 120), dtype=np.uint16)


@pytest.fixture
def sample_sar_image() -> np.ndarray:
    """Create a sample SAR image (single band, float)."""
    return np.random.exponential(1.0, (1, 256, 256)).astype(np.float32)


@pytest.fixture
def sample_temporal_pair(sample_rs_data_object: RSDataObject) -> tuple[RSDataObject, RSDataObject]:
    """Create a before/after image pair."""
    meta2 = RSMetadata(
        crs="EPSG:32633",
        transform=None,
        bounds=(0.0, 0.0, 100.0, 100.0),
        resolution=(10.0, 10.0),
        band_count=3,
        band_names=["B02", "B03", "B04"],
        dtype="uint8",
        nodata=None,
        width=256,
        height=256,
        file_format="GeoTIFF",
        acquisition_date="2023-11-01T10:00:00Z",
    )
    img2 = RSDataObject(
        data=np.random.randint(0, 255, (3, 256, 256), dtype=np.uint8),
        metadata=meta2,
        source_path=None,
        image_id="test_img_02",
    )
    return (sample_rs_data_object, img2)


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with default (mock) backend."""
    settings = Settings()
    settings.model.backend_type = "MOCK"
    return settings


@pytest.fixture
def test_app(test_settings: Settings):
    """Create test FastAPI app."""
    from backend.core.config import get_settings
    app = create_app(settings=test_settings)
    app.dependency_overrides[get_settings] = lambda: test_settings
    return app


@pytest_asyncio.fixture
async def test_client(test_app):
    """Create test HTTP client."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://testserver/api/v1",
    ) as client:
        yield client

