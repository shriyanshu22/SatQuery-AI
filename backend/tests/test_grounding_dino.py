"""Unit tests for GroundingDINOModel.

These tests use ``unittest.mock`` to avoid downloading the real
Grounding DINO weights so they can run in CI without a GPU.
"""

from __future__ import annotations

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from backend.core.evidence import BoundingBox


# ---------------------------------------------------------------------------
# Query normalisation (pure logic, no model needed)
# ---------------------------------------------------------------------------

class TestQueryNormalisation:
    """Tests for GroundingDINOModel._normalise_query."""

    @pytest.fixture(autouse=True)
    def _import_model(self):
        from backend.models.grounding_dino import GroundingDINOModel
        self.normalise = GroundingDINOModel._normalise_query

    def test_simple_label(self):
        """A bare label gets the trailing ' .' appended."""
        assert self.normalise("buildings") == "buildings ."

    def test_strips_where_prefix(self):
        """'Where are the X' → 'x .'."""
        assert self.normalise("Where are the buildings?") == "buildings ."

    def test_strips_locate_prefix(self):
        """'Locate the X' → 'x .'."""
        assert self.normalise("Locate the basketball court") == "basketball court ."

    def test_strips_find_prefix(self):
        """'Find the X' → 'x .'."""
        assert self.normalise("Find the roads") == "roads ."

    def test_preserves_existing_separator(self):
        """If the query already has ' . ' separators, leave it alone."""
        assert self.normalise("building . road .") == "building . road ."

    def test_case_insensitive(self):
        """Prefix stripping is case-insensitive."""
        assert self.normalise("WHERE IS THE river?") == "river ."


# ---------------------------------------------------------------------------
# Adapter lifecycle (mocked transformers)
# ---------------------------------------------------------------------------

class TestGroundingDINOLifecycle:
    """Tests for load / unload / is_loaded."""

    @patch("backend.models.grounding_dino.HAS_TRANSFORMERS", True)
    @patch("backend.models.grounding_dino.AutoModelForZeroShotObjectDetection")
    @patch("backend.models.grounding_dino.AutoProcessor")
    @patch("backend.models.grounding_dino.torch")
    def test_lazy_loading(self, mock_torch, mock_processor, mock_model):
        """Model should not be loaded until load() is called."""
        mock_torch.cuda.is_available.return_value = False

        from backend.models.grounding_dino import GroundingDINOModel

        m = GroundingDINOModel()
        assert not m.is_loaded()

        m.load()
        assert m.is_loaded()
        mock_processor.from_pretrained.assert_called_once()
        mock_model.from_pretrained.assert_called_once()

    @patch("backend.models.grounding_dino.HAS_TRANSFORMERS", True)
    @patch("backend.models.grounding_dino.AutoModelForZeroShotObjectDetection")
    @patch("backend.models.grounding_dino.AutoProcessor")
    @patch("backend.models.grounding_dino.torch")
    def test_unload(self, mock_torch, mock_processor, mock_model):
        """Unloading should release references."""
        mock_torch.cuda.is_available.return_value = False

        from backend.models.grounding_dino import GroundingDINOModel

        m = GroundingDINOModel()
        m.load()
        m.unload()
        assert not m.is_loaded()

    @patch("backend.models.grounding_dino.HAS_TRANSFORMERS", False)
    def test_missing_transformers(self):
        """Raise RuntimeError if transformers is not installed."""
        from backend.models.grounding_dino import GroundingDINOModel

        m = GroundingDINOModel()
        with pytest.raises(RuntimeError, match="transformers"):
            m.load()

    def test_get_model_info_before_load(self):
        """get_model_info() should work without loading the model."""
        from backend.models.grounding_dino import GroundingDINOModel

        m = GroundingDINOModel()
        info = m.get_model_info()
        assert info.name == "IDEA-Research/grounding-dino-tiny"
        assert info.device is None


# ---------------------------------------------------------------------------
# Inference (mocked)
# ---------------------------------------------------------------------------

class TestGroundingDINOInference:
    """Tests for the ground() method with mocked transformers."""

    @patch("backend.models.grounding_dino.HAS_TRANSFORMERS", True)
    @patch("backend.models.grounding_dino.AutoModelForZeroShotObjectDetection")
    @patch("backend.models.grounding_dino.AutoProcessor")
    @patch("backend.models.grounding_dino.torch")
    def test_ground_returns_boxes(self, mock_torch, mock_proc_cls, mock_model_cls):
        """ground() should return GroundingResult with BoundingBox objects."""
        import torch as real_torch

        mock_torch.cuda.is_available.return_value = False
        mock_torch.no_grad.return_value.__enter__ = MagicMock()
        mock_torch.no_grad.return_value.__exit__ = MagicMock()

        # Mock processor
        mock_processor = MagicMock()
        mock_proc_cls.from_pretrained.return_value = mock_processor
        mock_processor.return_value = MagicMock(
            input_ids=real_torch.tensor([[1, 2, 3]]),
            to=MagicMock(return_value=MagicMock(input_ids=real_torch.tensor([[1, 2, 3]])))
        )
        # Make inputs.to() return an object with input_ids
        mock_inputs = MagicMock()
        mock_inputs.input_ids = real_torch.tensor([[1, 2, 3]])
        mock_processor.return_value.to.return_value = mock_inputs

        # Mock model
        mock_model = MagicMock()
        mock_model.device = "cpu"
        mock_model_cls.from_pretrained.return_value.to.return_value = mock_model

        # Mock post-processing output
        mock_processor.post_process_grounded_object_detection.return_value = [
            {
                "scores": real_torch.tensor([0.85, 0.42]),
                "labels": ["building", "road"],
                "boxes": real_torch.tensor([
                    [10.0, 20.0, 100.0, 150.0],
                    [200.0, 300.0, 400.0, 500.0],
                ]),
            }
        ]

        from backend.models.grounding_dino import GroundingDINOModel

        m = GroundingDINOModel()
        m.load()

        image = np.zeros((3, 100, 100), dtype=np.uint8)
        result = m.ground(image, "buildings")

        assert len(result.boxes) == 2
        assert isinstance(result.boxes[0], BoundingBox)
        assert result.boxes[0].label == "building"
        assert result.boxes[0].confidence == 0.85
        assert result.raw_output["num_detections"] == 2
        assert result.raw_output["inference_duration_ms"] >= 0.0

    @patch("backend.models.grounding_dino.HAS_TRANSFORMERS", True)
    @patch("backend.models.grounding_dino.AutoModelForZeroShotObjectDetection")
    @patch("backend.models.grounding_dino.AutoProcessor")
    @patch("backend.models.grounding_dino.torch")
    def test_empty_detections(self, mock_torch, mock_proc_cls, mock_model_cls):
        """ground() should return empty boxes and unavailable confidence when nothing is detected."""
        import torch as real_torch

        mock_torch.cuda.is_available.return_value = False
        mock_torch.no_grad.return_value.__enter__ = MagicMock()
        mock_torch.no_grad.return_value.__exit__ = MagicMock()

        mock_processor = MagicMock()
        mock_proc_cls.from_pretrained.return_value = mock_processor

        mock_inputs = MagicMock()
        mock_inputs.input_ids = real_torch.tensor([[1, 2, 3]])
        mock_processor.return_value.to.return_value = mock_inputs

        mock_model = MagicMock()
        mock_model.device = "cpu"
        mock_model_cls.from_pretrained.return_value.to.return_value = mock_model

        # No detections
        mock_processor.post_process_grounded_object_detection.return_value = [
            {
                "scores": real_torch.tensor([]),
                "labels": [],
                "boxes": real_torch.tensor([]).reshape(0, 4),
            }
        ]

        from backend.models.grounding_dino import GroundingDINOModel

        m = GroundingDINOModel()
        m.load()

        image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = m.ground(image, "nonexistent objects")

        assert len(result.boxes) == 0
        assert result.confidence.value is None
        assert result.confidence.source == "unavailable"


# ---------------------------------------------------------------------------
# Routing tests
# ---------------------------------------------------------------------------

class TestGroundingRouting:
    """Tests for query routing to the grounding service."""

    def test_locate_routes_to_grounding(self):
        """A 'locate' query should be routed to GROUNDING."""
        from backend.agents.router import route_query
        from backend.api.schemas import QueryRequest

        req = QueryRequest(query="Locate the buildings", image_ids=["test"])
        intent = route_query(req)
        from backend.core.types import QueryIntent
        assert intent == QueryIntent.GROUNDING

    def test_find_routes_to_grounding(self):
        """A 'find' query should be routed to GROUNDING."""
        from backend.agents.router import route_query
        from backend.api.schemas import QueryRequest

        req = QueryRequest(query="Find the roads in this image", image_ids=["test"])
        intent = route_query(req)
        from backend.core.types import QueryIntent
        assert intent == QueryIntent.GROUNDING

    def test_where_routes_to_grounding(self):
        """A 'where' query should be routed to GROUNDING."""
        from backend.agents.router import route_query
        from backend.api.schemas import QueryRequest

        req = QueryRequest(query="Where are the buildings?", image_ids=["test"])
        intent = route_query(req)
        from backend.core.types import QueryIntent
        assert intent == QueryIntent.GROUNDING

    def test_what_routes_to_vqa(self):
        """A 'what' query should remain VQA."""
        from backend.agents.router import route_query
        from backend.api.schemas import QueryRequest

        req = QueryRequest(query="What objects are visible?", image_ids=["test"])
        intent = route_query(req)
        from backend.core.types import QueryIntent
        assert intent == QueryIntent.VQA
