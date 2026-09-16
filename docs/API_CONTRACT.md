# API Contract Specification

**Base URL**: `/api/v1`
**Authentication**: None (Local development mode)

## 1. Endpoints Overview
- `POST /upload`: Upload images
- `POST /query`: Submit a multimodal query
- `GET /status/{task_id}`: Check task progress
- `GET /result/{task_id}`: Fetch task output
- `GET /capabilities`: List available models/tools
- `GET /health`: Health check
- `GET /demo/samples`: List demo data
- `POST /demo/query`: Submit demo query

## 2. Detailed Specifications

### `POST /upload`
**Description**: Upload image(s) for a session.
**Request**: `multipart/form-data`
- `files`: Array of files (GeoTIFF, PNG, JPEG). Max 50MB per file.
- `metadata`: JSON string with CRS/Bands info (optional).
**Response (200 OK)**:
```json
{
  "session_id": "uuid-1234",
  "files": [
    {"file_id": "file-1", "filename": "img1.tif", "type": "optical"}
  ]
}
```

### `POST /query`
**Description**: Submit a text query alongside uploaded file IDs.
**Request (application/json)**:
```json
{
  "session_id": "uuid-1234",
  "query": "Find all airplanes in the image.",
  "file_ids": ["file-1"],
  "task_type": "auto" 
}
```
**Response (202 Accepted)**:
```json
{
  "task_id": "task-uuid",
  "status": "processing"
}
```

### `GET /status/{task_id}`
**Description**: Polling endpoint for long-running inferences.
**Response (200 OK)**:
```json
{
  "task_id": "task-uuid",
  "status": "completed" // or pending, failed
}
```

### `GET /result/{task_id}`
**Description**: Retrieve the final multimodal response and evidence.
**Response (200 OK)**:
```json
{
  "task_id": "task-uuid",
  "answer": "There are 3 airplanes detected.",
  "evidence": [
    {
      "type": "bounding_box",
      "data": [10.5, 20.1, 40.2, 50.8],
      "confidence": {"value": 0.92, "source": "GroundingDINO"}
    }
  ],
  "agent_trace": ["Routed to Grounding service."]
}
```

## 3. Error Responses
All errors follow standard RFC 7807 Problem Details or basic Pydantic validation arrays.
```json
{
  "error": "Validation Error",
  "detail": "Missing session_id."
}
```
- **400**: Bad Request (Invalid JSON)
- **404**: Not Found (Task ID missing)
- **422**: Unprocessable Entity (Pydantic validation failure)
- **500**: Internal Server Error

## 4. Rate Limiting
Not enforced for local MVP. Hooks placed in middleware.

## 5. File Upload Spec
- Allowed formats: `image/tiff`, `image/png`, `image/jpeg`
- Size limit: 100 MB aggregate.

## 6. Example cURL
```bash
curl -X POST http://localhost:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{"session_id":"123","query":"Is there change?","file_ids":["f1","f2"]}'
```

## 7. Versioning Strategy
API versioned via URL path (`/api/v1`). V2 will be used if breaking changes to Evidence data structures occur.
