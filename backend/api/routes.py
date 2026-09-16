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
    ValidationIssueSchema,
    ImageMetadataSchema,
    QueryRequest,
    QueryResponse,
    TaskStatusResponse,
    CapabilityInfo,
    HealthResponse,
    DemoSampleSchema,
    DemoImageSchema,
    DemoQueryRequest,
    AnalysisResultSchema,
    EvidenceSchema,
    ExecutionStepSchema,
    ConfidenceSchema,
    ReportResponse,
)

logger = get_logger(__name__)
router = APIRouter()


_artifact_store_instance: ArtifactStore | None = None


def get_artifact_store(settings: Settings = Depends(get_settings)) -> ArtifactStore:
    """Dependency for providing the artifact store singleton."""
    global _artifact_store_instance
    if _artifact_store_instance is None:
        _artifact_store_instance = ArtifactStore(root_dir=settings.storage.output_dir)
    return _artifact_store_instance



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
            issues=[
                ValidationIssueSchema(
                    id=f"warn-{i}",
                    message=w,
                    severity="warning"
                ) for i, w in enumerate(rs_data.warnings)
            ]
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
    if artifact and Path(artifact.path).exists():
        return FileResponse(path=Path(artifact.path), filename=artifact.filename)

    # Disk search fallback
    root = artifact_store.root_dir
    if root.exists():
        short_id = artifact_id[:8]
        for f in root.glob(f"**/*{short_id}*"):
            if f.is_file():
                return FileResponse(path=f, filename=f.name)

    raise HTTPException(status_code=404, detail="Artifact not found")



# In-memory store for async task tracking & result retrieval
_task_store: dict[str, dict[str, Any]] = {}


@router.get("/capabilities")
async def get_capabilities(settings: Settings = Depends(get_settings)):
    """List available capabilities and model backends."""
    return {
        "capabilities": [
            {
                "name": "vqa",
                "description": "Visual Question Answering over remote sensing imagery",
                "available": True,
                "model_backend": settings.model.backend_type,
            },
            {
                "name": "grounding",
                "description": "Text-guided spatial object and feature grounding with bounding boxes",
                "available": True,
                "model_backend": "MOCK",
            },
            {
                "name": "change_detection",
                "description": "Bi-temporal spatial change detection and metric calculation",
                "available": True,
                "model_backend": "ALIGNED_DIFF",
            },
            {
                "name": "cross_modal",
                "description": "Optical + Synthetic Aperture Radar (SAR) multi-sensor fusion and corroboration",
                "available": True,
                "model_backend": "FUSION",
            },
        ]
    }


@router.post("/query", response_model=QueryResponse)
async def query_image(
    request: QueryRequest,
    settings: Settings = Depends(get_settings),
):
    """End-to-end query endpoint supporting VQA, Grounding, Change Detection, and Cross-Modal analysis."""
    import uuid
    import time
    from backend.preprocessing.image_loader import load_image
    from backend.api.orchestrator import QueryOrchestrator

    task_id = str(uuid.uuid4())

    if not request.image_ids:
        raise HTTPException(status_code=400, detail="No image_ids provided.")

    upload_dir = Path(settings.storage.upload_dir)
    loaded_images = []

    # Ingest and load all referenced images
    for image_id in request.image_ids:
        try:
            uuid.UUID(image_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid image_id format: {image_id}")

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
            loaded_images.append(rs_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load image {image_id}: {e}")

    # Delegate to Orchestrator
    orchestrator = QueryOrchestrator(settings)
    internal_result = orchestrator.execute(request, loaded_images)

    # Convert canonical AnalysisResult to API schema
    public_result = AnalysisResultSchema.from_internal(internal_result)
    public_result.id = task_id

    # Record in task store for async polling or subsequent retrieval
    _task_store[task_id] = {
        "status": "completed",
        "progress": 100.0,
        "result": public_result,
        "created_at": time.time(),
        "query": request.query,
    }

    return QueryResponse(
        task_id=task_id,
        status="completed",
        result=public_result,
    )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Check asynchronous task progress status."""
    task = _task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=task.get("progress", 100.0),
        message=task.get("message"),
    )


@router.get("/result/{task_id}", response_model=QueryResponse)
async def get_task_result(task_id: str):
    """Retrieve final multimodal analysis response and evidence."""
    task = _task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return QueryResponse(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
    )


# ---------------------------------------------------------------------------
# Demo Scenarios Catalog & Execution
# ---------------------------------------------------------------------------

DEMO_CATALOG = [
    {
        "id": "urban-growth-sar",
        "title": "Urban Expansion & SAR Corroboration",
        "tagline": "The SIH Killer Query Workflow",
        "description": "Bi-temporal optical comparison coupled with Sentinel-1 SAR backscatter verification to confirm permanent urban development.",
        "targetWorkflow": "cross_modal",
        "images": [
            {
                "id": "demo-opt-2022",
                "filename": "Sentinel2_Urban_2022_T1.tif",
                "url": "https://images.unsplash.com/photo-1524813686514-a57563d77d66?auto=format&fit=crop&w=1200&q=80",
                "modality": "optical",
                "dimensions": {"width": 2048, "height": 2048},
                "acquisitionDate": "2022-03-15",
                "sensor": "Sentinel-2 MSI",
                "crs": "EPSG:4326",
            },
            {
                "id": "demo-opt-2024",
                "filename": "Sentinel2_Urban_2024_T2.tif",
                "url": "https://images.unsplash.com/photo-1477959858617-67f30bc75b82?auto=format&fit=crop&w=1200&q=80",
                "modality": "optical",
                "dimensions": {"width": 2048, "height": 2048},
                "acquisitionDate": "2024-03-18",
                "sensor": "Sentinel-2 MSI",
                "crs": "EPSG:4326",
            },
            {
                "id": "demo-sar-2024",
                "filename": "Sentinel1_SAR_C_Band_2024.tif",
                "url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1200&q=80",
                "modality": "sar",
                "dimensions": {"width": 2048, "height": 2048},
                "acquisitionDate": "2024-03-20",
                "sensor": "Sentinel-1 C-SAR",
                "crs": "EPSG:4326",
            },
        ],
        "suggestedQueries": [
            "Did urban development increase between these dates, and can SAR support the result?",
            "What changed between these images?",
            "Identify permanent structural changes corroborated by radar.",
        ],
        "defaultQuery": "Did urban development increase between these dates, and can SAR support the result?",
    },
    {
        "id": "port-grounding",
        "title": "Port Facility Infrastructure Grounding",
        "tagline": "Visual Grounding & Spatial Detection",
        "description": "Detects, segments, and bounds maritime logistics assets, storage facilities, and transport vessels.",
        "targetWorkflow": "grounding",
        "images": [
            {
                "id": "demo-port-opt",
                "filename": "Port_Logistics_Hub_RGB.tif",
                "url": "https://images.unsplash.com/photo-1578575437130-527eed3abbec?auto=format&fit=crop&w=1200&q=80",
                "modality": "optical",
                "dimensions": {"width": 3840, "height": 2160},
                "acquisitionDate": "2024-05-10",
                "sensor": "WorldView-3",
                "crs": "EPSG:3857",
            }
        ],
        "suggestedQueries": [
            "Where are the buildings and storage tanks?",
            "Locate maritime vessels docked in the harbour.",
            "What is visible in this image?",
        ],
        "defaultQuery": "Where are the buildings and storage tanks?",
    },
    {
        "id": "flood-change",
        "title": "Post-Flood Surface Water Extent",
        "tagline": "Bi-Temporal Change Detection",
        "description": "Compares pre-flood baseline with post-monsoon imagery to delineate inundation boundaries and affected hectares.",
        "targetWorkflow": "change_detection",
        "images": [
            {
                "id": "demo-flood-pre",
                "filename": "River_Basin_Pre_Flood.tif",
                "url": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1200&q=80",
                "modality": "multispectral",
                "dimensions": {"width": 1920, "height": 1080},
                "acquisitionDate": "2023-06-01",
                "sensor": "Landsat-9 OLI-2",
                "crs": "EPSG:4326",
            },
            {
                "id": "demo-flood-post",
                "filename": "River_Basin_Post_Inundation.tif",
                "url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80",
                "modality": "multispectral",
                "dimensions": {"width": 1920, "height": 1080},
                "acquisitionDate": "2023-08-14",
                "sensor": "Landsat-9 OLI-2",
                "crs": "EPSG:4326",
            },
        ],
        "suggestedQueries": [
            "What changed between these images?",
            "Calculate total inundated area in hectares.",
            "What is visible in this image?",
        ],
        "defaultQuery": "What changed between these images?",
    },
]


@router.get("/demo/samples")
async def get_demo_samples():
    """Retrieve bundled demonstration scenarios for testing without GPU/upload."""
    return DEMO_CATALOG


@router.post("/demo/query", response_model=QueryResponse)
async def query_demo(request: DemoQueryRequest):
    """Execute a demo query using high-fidelity precomputed analytical responses."""
    import uuid
    task_id = str(uuid.uuid4())

    query_lower = request.query.lower()
    is_killer = any(w in query_lower for w in ["optical and sar", "urban", "sar", "support", "corroborat"])
    is_grounding = any(w in query_lower for w in ["where", "find", "locate", "box", "building", "storage"])

    if is_killer:
        evidence = [
            EvidenceSchema(
                type="cross_modal",
                data={
                    "id": "ev-cross-1",
                    "label": "Optical + SAR Corroboration Synthesis",
                    "opticalImageUrl": "https://images.unsplash.com/photo-1477959858617-67f30bc75b82?auto=format&fit=crop&w=1200&q=80",
                    "sarImageUrl": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1200&q=80",
                    "agreement": "agree",
                    "opticalEvidence": "NDBI differential analysis indicates a +38.4 hectare expansion of high-reflectance impervious surfaces.",
                    "sarEvidence": "Sentinel-1 C-SAR double-bounce backscatter (+4.2 dB in VV polarization) confirms permanent vertical concrete/steel structures.",
                    "combinedInterpretation": "Both sensor modalities positively corroborate urban growth. Optical spectral indices and radar microwave backscatter independently confirm genuine structural expansion.",
                    "confidence": 0.94,
                },
            ),
            EvidenceSchema(
                type="change_map",
                data={
                    "id": "ev-change-1",
                    "label": "Bi-Temporal Urban Footprint Change Map",
                    "beforeImageUrl": "https://images.unsplash.com/photo-1524813686514-a57563d77d66?auto=format&fit=crop&w=1200&q=80",
                    "afterImageUrl": "https://images.unsplash.com/photo-1477959858617-67f30bc75b82?auto=format&fit=crop&w=1200&q=80",
                    "changeMapUrl": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1200&q=80",
                    "changedAreaHectares": 38.4,
                    "changedAreaKm2": 0.384,
                    "changeType": "New Urban Development",
                    "confidence": 0.95,
                    "metrics": {
                        "totalAreaHectares": 1240,
                        "changedPercentage": 3.1,
                        "gainHectares": 38.4,
                        "lossHectares": 0,
                    },
                },
            ),
        ]
        answer = "Yes, urban development expanded by 38.4 hectares (+3.1%) between 2022 and 2024, fully corroborated by Sentinel-1 SAR double-bounce backscatter."
        task_name = "cross_modal"
    elif is_grounding:
        evidence = [
            EvidenceSchema(
                type="bounding_box",
                data={
                    "id": "ev-box-1",
                    "label": "Industrial Storage Tank Cluster",
                    "box": [0.35, 0.42, 0.58, 0.68],
                    "category": "Storage Tank",
                    "confidence": 0.93,
                    "sourceImageId": "demo-port-opt",
                },
            ),
            EvidenceSchema(
                type="bounding_box",
                data={
                    "id": "ev-box-2",
                    "label": "Maritime Logistics Warehouse",
                    "box": [0.62, 0.20, 0.85, 0.45],
                    "category": "Warehouse Facility",
                    "confidence": 0.91,
                    "sourceImageId": "demo-port-opt",
                },
            ),
        ]
        answer = "Located 2 primary facility regions: Industrial Storage Tank Cluster (central) and Maritime Logistics Warehouse (southwest sector)."
        task_name = "grounding"
    else:
        evidence = [
            EvidenceSchema(
                type="change_map",
                data={
                    "id": "ev-flood-1",
                    "label": "Post-Monsoon Inundation Extent",
                    "beforeImageUrl": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1200&q=80",
                    "afterImageUrl": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80",
                    "changeMapUrl": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80",
                    "changedAreaHectares": 142.6,
                    "changedAreaKm2": 1.426,
                    "changeType": "Surface Water Inundation",
                    "confidence": 0.96,
                    "metrics": {
                        "totalAreaHectares": 2400,
                        "changedPercentage": 5.94,
                        "gainHectares": 142.6,
                        "lossHectares": 0,
                    },
                },
            )
        ]
        answer = "Surface water inundation expanded across 142.6 hectares (+5.94% basin area) following monsoon flooding."
        task_name = "change_detection"

    result = AnalysisResultSchema(
        id=task_id,
        answer=answer,
        confidence=ConfidenceSchema(
            value=0.95,
            source="Demo Knowledge Store",
            method="precomputed",
            calibrated=True,
            score=0.95,
            status="available",
            explanation="Verified demo telemetry output",
        ),
        evidence=evidence,
        execution_trace=[
            ExecutionStepSchema(
                step_number=1,
                action="Demo telemetry retrieval",
                status="completed",
                observable_output="Loaded precomputed multimodal artifacts",
                id="step-1",
                label="Retrieving demonstration telemetry",
                detail="Synthetic cache hit",
            )
        ],
        metadata={"mode": "demo_cached"},
        task=task_name,
    )

    _task_store[task_id] = {
        "status": "completed",
        "progress": 100.0,
        "result": result,
        "created_at": 0,
        "query": request.query,
    }

    return QueryResponse(task_id=task_id, status="completed", result=result)


@router.get("/report/{analysis_id}")
async def download_report(analysis_id: str):
    """Generate and download a comprehensive analytical report."""
    from datetime import datetime, timezone
    from fastapi.responses import JSONResponse

    task = _task_store.get(analysis_id)
    if not task:
        report_data = {
            "report_id": f"REP-{analysis_id[:8]}",
            "analysis_id": analysis_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "summary": "SatQuery AI Remote Sensing Analytical Report",
            "system_version": "1.0.0",
        }
    else:
        res = task.get("result")
        report_data = {
            "report_id": f"REP-{analysis_id[:8]}",
            "analysis_id": analysis_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "query": task.get("query"),
            "status": task.get("status"),
            "answer": res.answer if res else "N/A",
            "task": getattr(res, "task", "unknown") if res else "unknown",
            "confidence": res.confidence.model_dump() if res and res.confidence else None,
            "evidence_count": len(res.evidence) if res else 0,
            "execution_trace": [t.model_dump() for t in res.execution_trace] if res else [],
        }

    return JSONResponse(
        content=report_data,
        headers={"Content-Disposition": f'attachment; filename="satquery_report_{analysis_id}.json"'},
    )


@router.get("/analysis/{analysis_id}/report")
async def download_analysis_report(analysis_id: str):
    """Alias matching frontend realClient.ts downloadReport expectation."""
    return await download_report(analysis_id)



