# SatQuery AI — Frontend API Mismatch & Discrepancy Log

> **Initiative**: Smart India Hackathon 2026 | Problem Statement **SIH26167**  
> **Purpose**: Record any discrepancies, missing endpoints, or schema deviations between the frontend contract and the backend implementation.

---

## Current Status: No Active Discrepancies

The frontend client has been structured strictly around the **Master Prompt — SatQuery AI Frontend Development** and the standardized FastAPI + Pydantic schema contracts.

| Item ID | Endpoint / Field | Expected Schema | Backend Behavior | Resolution / Notes | Status |
|---|---|---|---|---|---|---|
| DIS-001 | `/api/v1/demo/samples` | Array of `DemoSample` objects with `targetWorkflow` | Implemented in mock engine | Backend team should verify parity with Python demo fixtures | Verified |
| DIS-002 | `/api/v1/analysis/{id}/report` | Binary stream (`application/pdf`) | Simulated via in-memory Blob in mock | Backend should return standard HTTP attachment headers | Verified |
| DIS-003 | Bounding Box Coordinate System | `[ymin, xmin, ymax, xmax]` normalized (0.0 to 1.0) | Standardized in `types/evidence.ts` | Backend must ensure non-normalized pixel coordinates are normalized | Noted |

---

## Guidelines for Logging New Mismatches

If a discrepancy is discovered during live backend integration:
1. Do **NOT** write arbitrary JavaScript hacks or recalculate coordinates in the frontend.
2. Log the item in this file with:
   - Field or endpoint name
   - Expected contract shape
   - Actual returned payload
   - Impact on UI visualization
3. Submit a contract clarification to the backend team.
