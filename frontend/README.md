# Frontend
The frontend for SatQuery AI is NOT implemented in this repository.

This repository focuses exclusively on the backend logic, model orchestration, and APIs for multimodal remote-sensing image analysis. The frontend will be developed independently by a separate team member.

## Backend-Frontend Contract
The frontend MUST communicate with the backend exclusively through the documented REST API. For details on the API structure and contracts, please reference:
- [docs/API_CONTRACT.md](../docs/API_CONTRACT.md)
- [docs/FRONTEND_CONTRACT.md](../docs/FRONTEND_CONTRACT.md)

### Key API Endpoints
- `POST /api/v1/query`: Submit a text query along with an optional image or region of interest.
- `POST /api/v1/upload`: Upload remote sensing images for analysis.
- `GET /api/v1/status`: Check system status and available models.
- `GET /api/v1/demo`: Fetch demo queries and data.

## Backend Capability
The backend is fully functional independently. It can be interacted with via:
- The REST API using tools like `curl` or Postman.
- The OpenAPI documentation interface (Swagger UI) at `/docs`.
- Included CLI scripts in `scripts/`.
- Automated test suites in `backend/tests/`.

## Getting Started for Frontend Developers
1. Clone this repository to run the backend locally.
2. Follow the `README.md` instructions to install backend dependencies and start the local server.
3. Access the OpenAPI specifications at `http://localhost:8000/docs` to understand the available endpoints, request/response formats, and data schemas.
4. Build your frontend to interface with these endpoints, ensuring proper handling of multipart/form-data for image uploads and JSON for queries.
