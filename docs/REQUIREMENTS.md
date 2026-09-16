# Requirements Breakdown

## 1. Feature Classification

| Feature | Classification | Description |
|---------|----------------|-------------|
| VQA on Optical | MANDATORY | Answer questions based on single optical images. |
| Text-Guided Grounding | MANDATORY | Provide bounding boxes based on text descriptions. |
| Bi-Temporal CD | MANDATORY | Pixel-level change detection on image pairs. |
| Cross-Modal (SAR+Opt)| USP | Fuse Optical and SAR inputs to answer complex queries. |
| Model Adaptation | USP | Fine-tuned weights/LoRA for RS domain adaptation. |
| Agentic Routing | MVP | Hybrid routing to determine correct model chain. |
| Evaluation Suite | MANDATORY | Scripted pipeline to evaluate model performance. |
| Frontend UI | OPTIONAL | Developed independently via API contract. |
| Heatmaps/Masks | COSMETIC | Returning visual masks rather than just bounding boxes. |

## 2. Mandatory Capabilities (15 Items)
1. **Single-image ingestion**: Handle GeoTIFF/PNG inputs with metadata.
2. **Text-query parsing**: Extract intent from natural language.
3. **Agent routing**: Route queries to VQA, Grounding, CD, or Cross-modal.
4. **VQA Inference**: Execute Vision-Language model for answers.
5. **Grounding Inference**: Execute detection models for bounding boxes.
6. **Change Detection**: Run Siamese networks for temporal changes.
7. **Cross-Modal alignment**: Verify optical and SAR spatial correspondence.
8. **Evidence Generation**: Output structured evidence for all claims.
9. **Confidence Scoring**: Assign true probabilities or mark as unavailable.
10. **Model Fallbacks**: Graceful fallback from GPU to CPU or mock modes.
11. **REST API**: Fully typed asynchronous interface.
12. **Demo Mode**: Genuine pre-cached output capabilities.
13. **Upload management**: Secure temporary storage of multi-channel data.
14. **Metric Logging**: Performance tracking (time, tokens).
15. **Error formatting**: User-friendly API error responses.

## 3. Product Principles
- **A. Integrity**: Never fabricate data.
- **B. Transparency**: Always return evidence and sources.
- **C. Independence**: Frontend and backend are completely decoupled.
- **D. Determinism**: Testing uses mock models for 100% reproducibility.
- **E. Flexibility**: Models can be swapped without touching domain logic.
- *(Remaining principles follow the core spec sheet)*

## 4. Non-Functional Requirements
- **Performance**: API response for non-inference tasks < 100ms. Inference handled asynchronously or via long-polling.
- **Reliability**: System handles broken GeoTIFFs gracefully (HTTP 422).
- **Security**: Uploaded files scanned for magic bytes. No direct execution of user data. Path traversal protection.
- **Extensibility**: Adding a new model merely requires implementing `ModelAdapter` protocol.

## 5. Assumptions and Constraints
- The backend will run on Windows environments for development (GPU availability depends on local hardware).
- Real inference requires CUDA-capable GPUs with at least 8GB VRAM (12GB+ recommended for 2B/3B models).
- No Git initialization is performed by the agent scaffolding process.

## 6. Glossary of Terms
- **RS**: Remote Sensing
- **VQA**: Visual Question Answering
- **SAR**: Synthetic Aperture Radar
- **VLM**: Vision-Language Model
- **GeoTIFF**: Standard format for RS imagery holding spatial metadata.
- **CRS**: Coordinate Reference System
- **CD**: Change Detection
- **LoRA**: Low-Rank Adaptation (Fine-tuning technique)
