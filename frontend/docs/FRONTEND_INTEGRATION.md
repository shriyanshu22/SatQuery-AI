# SatQuery AI — Frontend Integration Guide

> **Initiative**: Smart India Hackathon 2026 | Problem Statement **SIH26167**  
> **Backend Stack**: FastAPI + Pydantic/OpenAPI + PyTorch / Remote Sensing Pipeline

---

## 1. Environment Configuration

The frontend client communicates with the backend exclusively via standard HTTP/REST endpoints configured via environment variables:

Create `.env` in `geolens-frontend-landing/satquery-ai/`:

```env
# Base URL of the FastAPI Backend
VITE_API_BASE_URL=http://localhost:8000

# API Mode: "mock" (offline in-browser simulation) or "real" (HTTP REST calls)
VITE_API_MODE=mock
```

---

## 2. Documented REST Endpoints

### 2.1 Backend Health Check
- **Method**: `GET`
- **Path**: `/health` (or `/api/v1/status`)
- **Response**:
```json
{
  "online": true,
  "mode": "real",
  "version": "1.0.0"
}
```

### 2.2 Remote Sensing Image Ingestion
- **Method**: `POST`
- **Path**: `/api/v1/images/upload`
- **Content-Type**: `multipart/form-data`
- **Parameters**: `file` (File binary: GeoTIFF, TIFF, Optical, SAR)
- **Response (200 OK)**:
```json
{
  "metadata": {
    "filename": "Sentinel2_Urban_2024.tif",
    "fileType": "image/tiff",
    "sizeBytes": 14680064,
    "width": 2048,
    "height": 2048,
    "bandCount": 3,
    "modality": "optical",
    "crs": "EPSG:4326",
    "acquisitionDate": "2024-03-18",
    "sensor": "Sentinel-2 MSI"
  },
  "validation": {
    "status": "valid",
    "issues": []
  },
  "remotePreviewUrl": "http://localhost:8000/static/previews/preview_xyz.jpg"
}
```

### 2.3 Query Submission
- **Method**: `POST`
- **Path**: `/api/v1/analysis/query`
- **Content-Type**: `application/json`
- **Request Body**:
```json
{
  "prompt": "Did urban development increase between these dates, and can SAR support the result?",
  "imageIds": ["img-1", "img-2", "img-3"]
}
```
- **Response (202 Accepted / 200 OK)**:
```json
{
  "id": "analysis-101",
  "queryId": "query-55",
  "status": "running",
  "executionTrace": [
    { "id": "step-0", "label": "Validating bi-temporal & SAR scenes", "status": "active" },
    { "id": "step-1", "label": "Aligning coordinate reference systems", "status": "pending" }
  ],
  "evidence": [],
  "warnings": []
}
```

### 2.4 Query Polling & Result Retrieval
- **Method**: `GET`
- **Path**: `/api/v1/analysis/{analysisId}`
- **Response (200 OK - When Complete)**:
```json
{
  "id": "analysis-101",
  "queryId": "query-55",
  "status": "succeeded",
  "task": "cross_modal",
  "answer": "Yes, urban development increased significantly (+38.4 hectares). SAR backscatter corroborates optical findings.",
  "confidence": {
    "status": "available",
    "score": 0.94,
    "method": "calibrated",
    "explanation": "Calibrated across optical NDBI and SAR backscatter permanence."
  },
  "executionTrace": [
    { "id": "step-0", "label": "Validating bi-temporal & SAR scenes", "status": "done" },
    { "id": "step-1", "label": "Computing optical NDBI", "status": "done" },
    { "id": "step-2", "label": "Analyzing SAR backscatter coherence", "status": "done" },
    { "id": "step-3", "label": "Compiling grounded evidence", "status": "done" }
  ],
  "evidence": [
    {
      "id": "ev-1",
      "type": "cross_modal",
      "label": "Optical + SAR Verification",
      "opticalImageUrl": "...",
      "sarImageUrl": "...",
      "agreement": "agree",
      "opticalEvidence": "NDBI indicates +38.4 ha expansion.",
      "sarEvidence": "VV backscatter +4.2 dB confirms structural permanence.",
      "combinedInterpretation": "Both sensors confirm genuine urban growth.",
      "confidence": 0.94
    },
    {
      "id": "ev-2",
      "type": "change_map",
      "label": "Urban Footprint Change Map",
      "beforeImageUrl": "...",
      "afterImageUrl": "...",
      "changeMapUrl": "...",
      "changedAreaHectares": 38.4
    }
  ],
  "warnings": [],
  "report": {
    "available": true,
    "downloadUrl": "/api/v1/analysis/analysis-101/report",
    "format": "pdf",
    "filename": "SatQuery_Report_101.pdf"
  }
}
```

### 2.5 Report Artifact Download
- **Method**: `GET`
- **Path**: `/api/v1/analysis/{analysisId}/report`
- **Response**: Binary stream (`application/pdf` or `application/octet-stream`)

---

## 3. Switching From Mock to Real Backend

1. Implement `src/api/real/realClient.ts` implementing `SatQueryApiClient`.
2. In `src/api/index.ts`, return `realClient` when `mode === 'real'`.
3. Set in `.env`:
   ```env
   VITE_API_MODE=real
   VITE_API_BASE_URL=http://localhost:8000
   ```
4. Restart development server. Zero UI components require modification.
