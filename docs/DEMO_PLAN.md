# Demo Plan

## 1. Purpose
The purpose of the Demo Mode is to demonstrate the real capabilities of SatQuery AI using bundled data, ensuring evaluators can test the system flawlessly regardless of their local hardware constraints (e.g., lack of a dedicated GPU).

## 2. Integrity and Real Components
**CRITICAL RULE**: The demo uses the *real pipeline components*. We do not use hard-coded `if query == "X" return "Y"` logic in the service layer.
Instead, we rely on the `CachedModelOutput` tier, which returns genuine, pre-computed outputs from the actual models based on the input hash.

## 3. Three Categories of Demo Output
1. **Live Inference**: If the evaluator has a capable GPU, the demo bundled images are passed to the `RealModel`.
2. **CachedModelOutput Replay**: If no GPU is available, the pipeline executes, but the `ModelAdapter` hits a cache layer for the bundled images, returning the *exact* evidence the real model produced previously.
3. **Mock Mode (Testing)**: Purely for developers, returns dummy data to test UI/API.

The response JSON will ALWAYS contain a `model_tier` field clearly labeling which mode generated the response.

## 4. Bundled Demo Images Plan
We will bundle 5-10 small, real satellite images (under Creative Commons or open-data licenses).
Location: `data/demo_samples/`
- `optical_urban.tif`
- `sar_urban.tif`
- `cd_time1.tif`, `cd_time2.tif`

## 5. Demo Scenarios
- **Scenario A (VQA)**: Image: `optical_urban.tif`. Query: "How many storage tanks are visible?"
- **Scenario B (Grounding)**: Image: `optical_urban.tif`. Query: "Locate all the airplanes." -> Returns bounding boxes.
- **Scenario C (Change Detection)**: Images: `cd_time1.tif`, `cd_time2.tif`. Query: "Where did deforestation occur?" -> Returns mask.
- **Scenario D (Cross-Modal)**: Images: `optical_urban.tif`, `sar_urban.tif`. Query: "Do the optical and SAR images agree on the bridge structure?"

## 6. API Endpoints for Demo
- `GET /demo/samples`: Returns metadata and paths for bundled demo images.
- `POST /demo/query`: Identical to `/query`, but optimized to utilize the `CachedModelOutput` layer explicitly to ensure speed during presentations.

## 7. UI Distinction
The frontend (per `FRONTEND_CONTRACT.md`) will display a badge (e.g., "⚡ Live AI" vs "🗄️ Cached Real AI") based on the `model_tier` output, maintaining absolute transparency with judges.
