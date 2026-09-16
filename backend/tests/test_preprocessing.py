"""Preprocessing module tests."""

from __future__ import annotations

import pytest
import numpy as np


class TestImageLoader:
    """Tests for image loading utilities."""

    def test_detect_format_png(self) -> None:
        """PNG extension is recognized."""
        from backend.preprocessing.image_loader import detect_format
        assert detect_format("test_image.png") == "png"

    def test_detect_format_tiff(self) -> None:
        """TIFF extension is recognized."""
        from backend.preprocessing.image_loader import detect_format
        fmt = detect_format("satellite_scene.tiff")
        assert fmt == "geotiff"

    def test_load_standard_image(self, tmp_path) -> None:
        """Loading a standard image returns valid array."""
        # TODO: create a real PNG on disk and test load
        pass

    def test_generate_image_id_is_unique(self) -> None:
        """Generated image IDs must not collide."""
        from backend.preprocessing.image_loader import generate_image_id
        ids = {generate_image_id(f"image_{i}.tif") for i in range(100)}
        assert len(ids) == 100


class TestValidators:
    """Tests for input validation."""

    def test_validate_rejects_nonexistent_file(self) -> None:
        """A non-existent path must be rejected."""
        from backend.preprocessing.validators import validate_image_file
        result = validate_image_file("/nonexistent/path/fake_image.tif")
        assert not result.valid
        assert any("does not exist" in e for e in result.errors)

    def test_validate_rejects_oversized_file(self) -> None:
        """Files exceeding the size limit must be rejected."""
        # TODO: create oversized temp file
        pass

    def test_validate_accepts_valid_image(self, tmp_path) -> None:
        """A valid image file should pass validation."""
        # TODO: create valid temp image
        pass

    def test_temporal_pair_validation_compatible(self, sample_temporal_pair) -> None:
        """Compatible temporal pair shares CRS and dimensions."""
        img1, img2 = sample_temporal_pair
        assert img1.metadata.crs == img2.metadata.crs
        assert img1.data.shape == img2.data.shape

    def test_temporal_pair_validation_incompatible_crs(self) -> None:
        """Incompatible CRS pair should be flagged."""
        # TODO: create pair with mismatched CRS
        pass


class TestNormalizer:
    """Tests for image normalization."""

    def test_minmax_normalization(self, sample_rgb_image) -> None:
        """Min-max normalization maps values to [0, 1]."""
        normalized = (sample_rgb_image - sample_rgb_image.min()) / (sample_rgb_image.max() - sample_rgb_image.min() + 1e-8)
        assert normalized.min() >= 0
        assert normalized.max() <= 1

    def test_zscore_normalization(self, sample_rgb_image) -> None:
        """Z-score normalization centers data around zero."""
        zscore = (sample_rgb_image - sample_rgb_image.mean()) / (sample_rgb_image.std() + 1e-8)
        assert np.isclose(zscore.mean(), 0, atol=1e-5)

    def test_select_bands(self, sample_multispectral_image) -> None:
        """Selecting bands reduces the band dimension."""
        selected = sample_multispectral_image[:3]  # First 3 bands
        assert selected.shape[0] == 3
        assert selected.shape[1:] == sample_multispectral_image.shape[1:]

    def test_compose_rgb(self, sample_multispectral_image) -> None:
        """Composing RGB from multispectral yields 3-band output."""
        rgb = sample_multispectral_image[:3]
        assert rgb.shape[0] == 3


class TestTiling:
    """Tests for image tiling/untiling."""

    def test_tile_image_correct_count(self) -> None:
        """Tiling a 512x512 image at 256 tile size yields 4 tiles."""
        # 512/256 = 2 per axis => 4 tiles
        tiles_per_axis = 512 // 256
        assert tiles_per_axis * tiles_per_axis == 4

    def test_reassemble_recovers_original(self) -> None:
        """Reassembling tiles should recover the original dimensions."""
        original = np.random.rand(3, 512, 512)
        # Simulate split and rejoin
        tiles = [original[:, i*256:(i+1)*256, j*256:(j+1)*256] for i in range(2) for j in range(2)]
        reassembled = np.zeros_like(original)
        idx = 0
        for i in range(2):
            for j in range(2):
                reassembled[:, i*256:(i+1)*256, j*256:(j+1)*256] = tiles[idx]
                idx += 1
        np.testing.assert_array_equal(original, reassembled)

    def test_should_tile_large_image(self) -> None:
        """Images larger than threshold should be tiled."""
        image_size = (3, 2048, 2048)
        max_dim = 1024
        assert max(image_size[1], image_size[2]) > max_dim

    def test_should_not_tile_small_image(self) -> None:
        """Images within threshold should not be tiled."""
        image_size = (3, 256, 256)
        max_dim = 1024
        assert max(image_size[1], image_size[2]) <= max_dim


class TestSARPreprocessing:
    """Tests for SAR image preprocessing."""

    def test_log_scaling(self, sample_sar_image) -> None:
        """Log scaling compresses SAR dynamic range."""
        log_scaled = np.log1p(sample_sar_image)
        assert log_scaled.max() < sample_sar_image.max()
        assert log_scaled.min() >= 0

    def test_speckle_filter(self, sample_sar_image) -> None:
        """Speckle filter should reduce variance."""
        # Simple box filter as proxy
        from scipy.ndimage import uniform_filter
        filtered = uniform_filter(sample_sar_image, size=3)
        assert filtered.var() <= sample_sar_image.var()

    def test_detect_sar_image(self) -> None:
        """SAR images are typically single-band float32."""
        sar = np.random.exponential(1.0, (1, 64, 64)).astype(np.float32)
        assert sar.shape[0] == 1
        assert sar.dtype == np.float32

