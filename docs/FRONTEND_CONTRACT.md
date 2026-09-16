# Frontend Integration Contract

## 1. Overview
The Frontend and Backend are strictly decoupled. The Frontend is developed independently and communicates with the Backend **exclusively** via the REST API defined in `API_CONTRACT.md`.
There is no shared state, no shared code repository (unless monorepo structure is explicitly adopted later), and no server-side HTML rendering.

## 2. Responsibility Division

### Frontend Responsibilities
- **UI Rendering**: Map components, chat interfaces, image upload forms.
- **State Management**: Session tracking, upload progress, polling task status.
- **Visualizations**: Drawing bounding boxes, overlaying change detection masks, and highlighting evidence on the images.
- **User Input**: Capturing text queries and file selections.
- **Error Display**: Translating API errors into user-friendly alerts.

### Backend Responsibilities (SatQuery AI)
- **Processing**: Handling complex ML inferences.
- **Data Responses**: Providing strictly typed JSON responses.
- **Evidence Generation**: Supplying raw coordinates, masks, and text.
- **API Spec**: Maintaining the OpenAPI (`/docs`) specification for frontend client generation.

## 3. Communication Patterns
- **CORS Configuration**: The backend FastAPI app will be configured with permissive CORS for local development (`localhost:3000`, `localhost:5173`, etc.).
- **File Upload Protocol**: 
  - Frontend must send files as `multipart/form-data`.
  - Backend responds with a `session_id` and `file_ids`.
- **Long-Running Task Pattern (Async)**:
  1. Frontend calls `POST /query`.
  2. Backend returns `202 Accepted` with a `task_id`.
  3. Frontend polls `GET /status/{task_id}` every ~2 seconds.
  4. Upon `status: "completed"`, Frontend calls `GET /result/{task_id}`.

## 4. Error Handling Expectations
- The Frontend must gracefully handle HTTP `422 Unprocessable Entity` (usually bad input) and `500 Internal Server Error` (often model/GPU failures).
- Backend errors include a `detail` field which the frontend can display for debugging.

## 5. Demo Mode Usage
- The Frontend should provide a "Try Demo" button.
- Clicking this calls `GET /demo/samples` to list available bundled images.
- When the user selects a demo scenario, the frontend calls `POST /demo/query`.
- The frontend must clearly display when the system is returning "Cached Model Output" vs "Live Inference".

## 6. Integration Testing Approach
- Frontend teams can use the `MockModel` configuration on the backend to test their UI without needing a GPU.
- The Backend OpenAPI schema can be exported to generate TypeScript clients automatically (e.g., via `openapi-ts`).
