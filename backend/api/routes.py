"""API route definitions."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from pydantic import ValidationError

from backend.core.logging import get_logger
from backend.core.config import get_settings, Settings
from backend.core.artifacts import ArtifactStore
from backend.preprocessing.image_loader import load_image
from backend.preprocessing.validators import validate_upload
from backend.preprocessing.modality import detect_modality
from backend.preprocessing.preview import generate_preview
from backend.api.schemas import (
    UploadResponse,
    ValidationResultSchema,
    ImageMetadataSchema,
    QueryRequest,
    QueryResponse,
)

logger = get_logger(__name__)
router = APIRouter()


def get_artifact_store(settings: Settings = Depends(get_settings)) -> ArtifactStore:
    """Dependency for providing the artifact store."""
    return ArtifactStore(root_dir=settings.storage.output_dir)


@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    """API health check."""
    return {
        "application": "SatQuery AI",
        "status": "ok",
        "environment": settings.server.environment if hasattr(settings.server, 'environment') else "development",
        "version": "1.0.0",
        "model_backend": settings.model.backend_type,
        "capabilities": ["upload", "health"]
    }


@router.post("/upload", response_model=UploadResponse, status_code=200)
async def upload_image(
    file: UploadFile = File(...),
    metadata: str | None = Form(None),
    settings: Settings = Depends(get_settings),
    artifact_store: ArtifactStore = Depends(get_artifact_store),
):
    """Upload a remote sensing image for processing.

    Validates the file, extracts spatial metadata, detects modality, and
    generates a preview visualization.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    # 1. Validate upload metadata (before saving to disk)
    content_type = file.content_type or "application/octet-stream"
    # Note: UploadFile.size is available in newer FastAPI/Starlette versions. 
    # If not, we validate size after writing or using spool limits.
    # We'll use file.size if available, else 0 and rely on the validator.
    file_size = getattr(file, "size", 0)
    
    upload_val = validate_upload(
        filename=file.filename,
        content_length=file_size,
        content_type=content_type,
        max_size_bytes=settings.storage.max_upload_size_mb * 1024 * 1024
    )
    if not upload_val.valid:
        raise HTTPException(status_code=422, detail=upload_val.errors[0])

    # Sanitize filename (basic basename to prevent path traversal)
    safe_filename = os.path.basename(file.filename)
    if not safe_filename or safe_filename == "." or safe_filename == "..":
        safe_filename = "unnamed_file"
        
    import uuid
    generated_id = str(uuid.uuid4())
    
    # Ensure upload directory exists
    upload_dir = Path(settings.storage.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file to disk using the image_id and original filename to prevent collisions
    storage_name = f"{generated_id}_{safe_filename}"
    file_path = upload_dir / storage_name
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file to disk.")
    finally:
        await file.close()

    # Verify actual file size after saving if `file.size` was 0
    actual_size = file_path.stat().st_size
    if actual_size > settings.storage.max_upload_size_mb * 1024 * 1024:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Upload exceeds maximum allowed size.")
    if actual_size == 0:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    # 2. Load and validate image using the data engine
    try:
        rs_data = load_image(str(file_path), image_id=generated_id)
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Failed to process image: {str(e)}")

    if not rs_data.validation_status.value.startswith("valid"):
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Invalid image: {rs_data.warnings}")

    # 3. Detect Modality
    modality, _ = detect_modality(rs_data.metadata)
    rs_data.modality = modality
    rs_data.metadata.modality = modality.value

    # 4. Generate Preview
    preview_id = None
    try:
        preview_id = generate_preview(rs_data, artifact_store=artifact_store)
    except Exception as e:
        logger.warning(f"Failed to generate preview for {rs_data.image_id}: {e}")
        rs_data.add_warning("Preview generation failed.")

    # 5. Construct Response
    return UploadResponse(
        image_id=rs_data.image_id,
        filename=safe_filename,
        file_format=rs_data.file_format,
        size_bytes=actual_size,
        validation=ValidationResultSchema(
            status=rs_data.validation_status.value,  # type: ignore
            warnings=rs_data.warnings,
            errors=[],
        ),
        metadata=ImageMetadataSchema(
            crs=rs_data.metadata.crs,
            resolution=rs_data.metadata.resolution,
            bounds=rs_data.metadata.bounds,
            band_count=rs_data.metadata.band_count,
            modality=rs_data.metadata.modality,
            acquisition_date=rs_data.metadata.acquisition_date,
            width=rs_data.metadata.width,
            height=rs_data.metadata.height,
        ),
        preview_url=f"/api/v1/artifacts/{preview_id}" if preview_id else None
    )


@router.get("/artifacts/{artifact_id}")
async def get_artifact(
    artifact_id: str,
    artifact_store: ArtifactStore = Depends(get_artifact_store)
):
    """Serve a generated artifact file by its ID."""
    from fastapi.responses import FileResponse
    artifact = artifact_store.get(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
        
    path = Path(artifact.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact file missing from disk")
        
    return FileResponse(
        path=path,
        filename=artifact.filename,
        # Let FastAPI guess media type from filename
    )


@router.post("/query", response_model=QueryResponse)
async def query_image(
    request: QueryRequest,
    settings: Settings = Depends(get_settings),
):
    """End-to-end query endpoint for VQA and Grounding."""
    import uuid
    from backend.preprocessing.image_loader import load_image
    from backend.api.orchestrator import QueryOrchestrator
    from backend.api.schemas import AnalysisResultSchema

    task_id = str(uuid.uuid4())
    
    if not request.image_ids:
        raise HTTPException(status_code=400, detail="No image_ids provided.")
        
    # Lookup using the strict generated UUID
    upload_dir = Path(settings.storage.upload_dir)
    image_id = request.image_ids[0]  # Just handle single image for now
    
    # Validate UUID format to prevent path traversal via image_id
    try:
        uuid.UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image_id format.")
        
    file_path = None
    if upload_dir.exists():
        for f in upload_dir.iterdir():
            if f.name.startswith(f"{image_id}_"):
                file_path = f
                break
                
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found.")

    try:
        rs_data = load_image(str(file_path), image_id=image_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load image: {e}")

    # Delegate to Orchestrator
    orchestrator = QueryOrchestrator()
    internal_result = orchestrator.execute(request, rs_data)
    
    # Convert canonical AnalysisResult to API schema
    public_result = AnalysisResultSchema.from_internal(internal_result)

    return QueryResponse(
        task_id=task_id,
        status="completed",
        result=public_result
    )

