"""API endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestHealthEndpoint:
    """Tests for GET /api/v1/health."""

    async def test_health_returns_200(self, test_client: AsyncClient) -> None:
        """Health endpoint must return 200 OK."""
        response = await test_client.get("/health")
        assert response.status_code == 200

    async def test_health_returns_status_ok(self, test_client: AsyncClient) -> None:
        """Response must include status='ok'."""
        response = await test_client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    async def test_health_returns_version(self, test_client: AsyncClient) -> None:
        """Response must include a version string."""
        response = await test_client.get("/health")
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)

    async def test_health_returns_application_name(self, test_client: AsyncClient) -> None:
        """Response must include application='SatQuery AI'."""
        response = await test_client.get("/health")
        data = response.json()
        assert data["application"] == "SatQuery AI"

    async def test_health_returns_environment(self, test_client: AsyncClient) -> None:
        """Response must include environment field."""
        response = await test_client.get("/health")
        data = response.json()
        assert "environment" in data


class TestRootRedirect:
    """Tests for root URL redirect."""

    async def test_root_redirects_to_docs(self, test_client: AsyncClient) -> None:
        """GET / should redirect to /docs."""
        response = await test_client.get("/", follow_redirects=False)
        # The base_url includes /api/v1 so root is at the app level;
        # use a client without the prefix for this test
        pass  # Route: requires separate client without /api/v1 prefix


class TestMiddleware:
    """Tests for SecurityMiddleware."""

    async def test_request_id_header(self, test_client: AsyncClient) -> None:
        """Every response must include X-Request-ID."""
        response = await test_client.get("/health")
        assert "x-request-id" in response.headers

    async def test_process_time_header(self, test_client: AsyncClient) -> None:
        """Every response must include X-Process-Time."""
        response = await test_client.get("/health")
        assert "x-process-time" in response.headers
        assert float(response.headers["x-process-time"]) >= 0


class TestQueryEndpoint:
    """Tests for query submission."""

    async def test_query_returns_400_without_image_ids(self, test_client: AsyncClient) -> None:
        """POST /query should 400 if image_ids are missing."""
        response = await test_client.post("/query", json={"query": "What is in this image?"})
        assert response.status_code == 400

    async def test_query_vqa_returns_result(self, test_client: AsyncClient, monkeypatch) -> None:
        """Test default VQA routing."""
        from backend.core.types import RSDataObject
        from backend.preprocessing import image_loader
        
        # Mock load_image to prevent actual disk reads
        def mock_load(*args, **kwargs):
            from backend.core.types import RSMetadata
            import numpy as np
            meta = RSMetadata(
                crs=None, transform=None, bounds=None, resolution=None,
                band_count=3, band_names=None, dtype="uint8", nodata=None,
                width=100, height=100, file_format="png", acquisition_date=None
            )
            return RSDataObject(
                data=np.zeros((3, 100, 100)), metadata=meta, source_path=None, image_id="12345678-1234-5678-1234-567812345678"
            )
            
        monkeypatch.setattr(image_loader, "load_image", mock_load)
        import backend.api.routes as api_routes
        monkeypatch.setattr(api_routes, "load_image", mock_load)
        
        # Create a dummy file in the test upload_dir so the path existence check passes
        import os
        from backend.core.config import get_settings
        settings = get_settings()
        os.makedirs(settings.storage.upload_dir, exist_ok=True)
        dummy_path = os.path.join(settings.storage.upload_dir, "12345678-1234-5678-1234-567812345678_dummy.tif")
        with open(dummy_path, "w") as f:
            f.write("fake")

        response = await test_client.post("/query", json={
            "query": "Is there a building here?",
            "image_ids": ["12345678-1234-5678-1234-567812345678"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "deterministic answer" in data["result"]["answer"]
        assert data["result"]["metadata"]["model"] == "mock-vlm"

    async def test_query_grounding_returns_result(self, test_client: AsyncClient, monkeypatch) -> None:
        """Test keyword-based Grounding routing."""
        from backend.core.types import RSDataObject
        from backend.preprocessing import image_loader
        
        # Mock load_image to prevent actual disk reads
        def mock_load(*args, **kwargs):
            from backend.core.types import RSMetadata
            import numpy as np
            meta = RSMetadata(
                crs=None, transform=None, bounds=None, resolution=None,
                band_count=3, band_names=None, dtype="uint8", nodata=None,
                width=100, height=100, file_format="png", acquisition_date=None
            )
            return RSDataObject(
                data=np.zeros((3, 100, 100)), metadata=meta, source_path=None, image_id="12345678-1234-5678-1234-567812345678"
            )
            
        monkeypatch.setattr(image_loader, "load_image", mock_load)
        import backend.api.routes as api_routes
        monkeypatch.setattr(api_routes, "load_image", mock_load)
        
        # Create a dummy file in the test upload_dir so the path existence check passes
        import os
        from backend.core.config import get_settings
        settings = get_settings()
        os.makedirs(settings.storage.upload_dir, exist_ok=True)
        dummy_path = os.path.join(settings.storage.upload_dir, "12345678-1234-5678-1234-567812345678_dummy.tif")
        with open(dummy_path, "w") as f:
            f.write("fake")

        # "locate" should trigger grounding in our temporary router
        response = await test_client.post("/query", json={
            "query": "locate the building",
            "image_ids": ["12345678-1234-5678-1234-567812345678"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "Found 1 regions" in data["result"]["answer"]
        assert data["result"]["metadata"]["model"] == "mock-grounding"
        
        # Check that bounding box evidence is present
        evidence = data["result"]["evidence"]
        bbox_evidence = [e for e in evidence if e["type"] == "bounding_box"]
        assert len(bbox_evidence) == 1
        
        # Check confidence serialization
        conf = data["result"]["confidence"]
        assert conf["value"] is not None
        assert conf["source"] == "model_logits"


class TestUploadEndpoint:
    """Tests for file upload and persistence."""

    import pytest
    
    @pytest.fixture(autouse=True)
    def setup_mock_data_engine(self, monkeypatch):
        from backend.core.types import RSDataObject, RSMetadata
        from backend.preprocessing import image_loader
        import numpy as np

        def mock_load(filepath: str, image_id: str | None = None) -> RSDataObject:
            meta = RSMetadata(
                crs="EPSG:32633", transform=None, bounds=(0,0,10,10), resolution=(10,10),
                band_count=1, band_names=None, dtype="uint16", nodata=None,
                width=100, height=100, file_format="geotiff", acquisition_date=None
            )
            return RSDataObject(
                data=np.zeros((1, 100, 100)), metadata=meta, source_path=filepath, image_id=image_id or "test_id"
            )
        monkeypatch.setattr(image_loader, "load_image", mock_load)
        
        # Also patch where it is imported in routes!
        import backend.api.routes as api_routes
        monkeypatch.setattr(api_routes, "load_image", mock_load)
        
    @pytest.fixture
    def test_image_bytes(self) -> bytes:
        return b"fake tiff content"

    async def test_upload_creates_image_id_and_differs_from_filename(self, test_client: AsyncClient, test_image_bytes: bytes) -> None:
        """1 & 2: upload creates image_id and it differs from filename."""
        files = {"file": ("test_img.tif", test_image_bytes, "image/tiff")}
        response = await test_client.post("/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "image_id" in data
        assert data["image_id"] != data["filename"]
        assert data["filename"] == "test_img.tif"

    async def test_query_using_unknown_image_id_returns_404(self, test_client: AsyncClient) -> None:
        """5: query using unknown image_id returns clean 404."""
        response = await test_client.post("/query", json={"query": "test", "image_ids": ["00000000-0000-0000-0000-000000000000"]})
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
    async def test_query_using_invalid_image_id_returns_400(self, test_client: AsyncClient) -> None:
        """Verify that malformed image IDs are rejected."""
        response = await test_client.post("/query", json={"query": "test", "image_ids": ["invalid-uuid"]})
        assert response.status_code == 400

    async def test_two_uploads_same_filename_independent(self, test_client: AsyncClient, test_image_bytes: bytes) -> None:
        """6: two uploads with the same filename receive different image_ids and remain independently retrievable."""
        files1 = {"file": ("same_name.tif", test_image_bytes, "image/tiff")}
        resp1 = await test_client.post("/upload", files=files1)
        id1 = resp1.json()["image_id"]

        files2 = {"file": ("same_name.tif", test_image_bytes, "image/tiff")}
        resp2 = await test_client.post("/upload", files=files2)
        id2 = resp2.json()["image_id"]

        assert id1 != id2

        # 3 & 4: uploaded image can be resolved using image_id and query succeeds
        q_resp1 = await test_client.post("/query", json={"query": "test", "image_ids": [id1]})
        assert q_resp1.status_code == 200

        q_resp2 = await test_client.post("/query", json={"query": "test", "image_ids": [id2]})
        assert q_resp2.status_code == 200

    async def test_upload_blocks_path_traversal(self, test_client: AsyncClient, test_image_bytes: bytes) -> None:
        """7: unsafe filenames do not escape the managed upload directory."""
        files = {"file": ("../../../etc/passwd.tif", test_image_bytes, "image/tiff")}
        response = await test_client.post("/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "passwd.tif"
        assert "/" not in data["filename"]
        assert "\\" not in data["filename"]


class TestDemoEndpoint:
    """Tests for demo mode (routes not yet implemented)."""

    async def test_demo_samples_returns_404_when_unimplemented(self, test_client: AsyncClient) -> None:
        """GET /demo/samples should 404 until the route is wired up."""
        response = await test_client.get("/demo/samples")
        assert response.status_code in (404, 405)

    async def test_demo_query_returns_result(self, test_client: AsyncClient) -> None:
        pass  # TODO: implement after /demo route exists

