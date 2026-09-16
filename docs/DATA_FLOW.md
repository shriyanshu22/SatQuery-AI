# Data Flow Specifications

## 1. Preprocessing Pipeline Flow
1. **Raw File Upload**: User uploads `.tif` file via API.
2. **Validation**: Magic bytes checked. File stored in temporary session directory.
3. **RasterIO Reader**: Read band metadata, CRS, and affine transform.
4. **Normalization**: Multiband (e.g., Sentinel-2 13-band) mapped to RGB or standardized 0-255 arrays.
5. **RS DataObject**: Instantiated in `core`. Contains normalized tensor + spatial metadata.
6. **Model Adapter**: Specific model (e.g., Qwen adapter) transforms tensor into model-specific input (e.g., PIL Image or specific resolution tensors).

## 2. Single-Image VQA Flow
1. API receives query string and `file_id`.
2. **Agent** parses intent -> Routes to `VQAService`.
3. `VQAService` retrieves `RS DataObject` via preprocessing.
4. **Model execution**: `ModelAdapter` executes inference (e.g., via Qwen2-VL).
5. **Evidence Creation**: Output parsed into TextEvidence.
6. API returns response to User.

## 3. Single-Image Grounding Flow
1. API receives "Find all buildings".
2. **Agent** routes to `GroundingService`.
3. `ModelAdapter` (Grounding DINO) processes image + text prompt.
4. **Post-processing**: Bounding boxes mapped back to original image CRS/coordinates.
5. **Evidence Creation**: `BBoxEvidence` objects created with confidence scores.
6. API returns structured JSON.

## 4. Bi-Temporal Change Detection Flow
1. **Validation**: Check if both inputs have overlapping CRS and extent.
2. **Alignment (Co-registration)**: If unaligned, align image 2 to image 1 based on spatial metadata.
3. **Detection**: Siamese CNN compares aligned patches.
4. **Regions**: Produce binary change map.
5. **Interpretation (Optional)**: VLM evaluates changed regions to explain *what* changed.
6. **Evidence**: `MaskEvidence` and `TextEvidence` fused.

## 5. Cross-Modal Analysis Flow (Optical + SAR)
1. Query: "Verify deforestation using SAR."
2. **Optical Specialist**: Analyzes optical image for missing trees. Generates Evidence A.
3. **SAR Specialist**: Analyzes SAR image (backscatter reduction). Generates Evidence B.
4. **Evidence Fusion**: Dedicated fusion module compares Evidence A and B.
5. **Agreement/Disagreement**: System determines if modalities agree.
6. Response generated with distinct attribution to both sources.

## 6. Multi-Step Query Flow
*Example*: "Did urban development increase and can SAR confirm?"
1. **LLM Planner** breaks down into DAG:
   - Task 1: CD on Optical T1/T2.
   - Task 2: SAR analysis on T2.
   - Task 3: Fuse findings.
2. Tasks executed asynchronously.
3. Aggregated Evidence passed to LLM for final synthesis.

## 7. Evidence Flow
- Every service outputs `Evidence` objects (Core).
- API aggregates them into the final JSON.
- Never fabricated. If a step fails, Evidence is empty, and Error is propagated.

## 8. Error/Failure Flow
1. Model Out of Memory -> Caught by adapter.
2. Adapter signals failure.
3. Service returns `Confidence(None, "GPU OOM")`.
4. API maps to 500 error or partial success if another model tier works.
