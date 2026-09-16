# REAL GROUNDING SMOKE TEST — SATQUERY AI

This document verifies the end-to-end integration of the real spatial grounding capability via the `GroundingDINOModel` adapter, proving that `IDEA-Research/grounding-dino-tiny` successfully identifies spatial objects from a text query on real hardware.

---

## 1. Hardware & Environment
- **Platform:** Python 3.11
- **ML Framework:** PyTorch with CUDA 12.6
- **GPU:** NVIDIA GeForce RTX 4050 Laptop GPU (6 GB VRAM)
- **Model Framework:** Hugging Face `transformers`

## 2. Model Configuration
- **Adapter:** `backend/models/grounding_dino.py` -> `GroundingDINOModel`
- **Identifier:** `IDEA-Research/grounding-dino-tiny`
- **Precision:** FP16
- **Box Threshold:** 0.30
- **Text Threshold:** 0.25

## 3. API Endpoint Tested
`POST /api/v1/query` with `REAL` backend selected in `Settings.model.backend_type`.

## 4. Grounding Execution Flow

### Query 1: "Where are the buildings?"
The router successfully classified the intent as `GROUNDING` based on the keyword "where".

- **Actual Normalised Query Sent to Model:** `buildings .`
- **Inference Time:** 1.12 seconds (first real inference after model load)
- **Detection Result:** 5 real spatial regions detected.

**Example Real Bounding Box Produced:**
```json
{
  "x": 80.956,
  "y": 0.511,
  "w": 374.960,
  "h": 252.787,
  "label": "buildings",
  "confidence": 0.576
}
```

### Query 2: "Locate the basketball court"
The router successfully classified the intent as `GROUNDING` based on the keyword "locate".

- **Actual Normalised Query Sent to Model:** `basketball court .`
- **Inference Time:** 0.25 seconds (warm inference)
- **Detection Result:** 1 real spatial region detected.

**Example Real Bounding Box Produced:**
```json
{
  "x": 5.444,
  "y": 0.050,
  "w": 791.733,
  "h": 799.673,
  "label": "court",
  "confidence": 0.3185
}
```

### Query 3 (Regression): "What objects are visible in this image?"
The router successfully fell back to the default `VQA` intent, maintaining full interoperability with `Qwen2.5-VL-3B-Instruct`.

## 5. Confidence Behavior
The `GroundingResult` leverages the real object-detection confidence output by the model. The model calculates the max confidence among all identified bounding boxes to represent the total answer confidence.
- E.g. max box confidence for buildings was `0.576`.
- Value natively matches the schema defined in `backend.core.confidence`.

## 6. Visual Evidence
Real visualizations were correctly drawn onto the RGB source image and successfully stored inside `outputs/visualizations/` without fabricating bounding boxes.
- `outputs\visualizations\grounding_9047aaad_Where_are_the_buildi.png`
- `outputs\visualizations\grounding_9047aaad_Locate_the_basketbal.png`

## 7. MOCK vs REAL Separation
The test suite continues to bypass the expensive download and GPU-loading by unconditionally injecting `MockGroundingModel` (`backend_type="MOCK"`). 76/76 unit tests pass smoothly in ~5.84s, strictly isolating mock models from real network/hardware dependencies.

## 8. Limitations & Edge Cases
- **Box Scaling:** Grounding DINO currently processes and predicts bounding boxes relative to pixel counts. Upstream tasks that want geolocated coordinates must mathematically transform the output utilizing the CRS and Bound parameters populated via `MetadataEvidence`.
- **Low Confidence Queries:** Extremely specific or abstract queries that fail the threshold test (0.30) cleanly return an empty list `[]` of BoundingBoxes, triggering a native "no regions detected" response instead of generating hallucinated boxes.
