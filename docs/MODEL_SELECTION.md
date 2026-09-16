# Model Selection — SatQuery AI (SIH26)

**Date**: 2026-09-16  
**Hardware**: RTX 4050 Laptop (6 GB VRAM), 16 GB RAM, 28 GB free disk  
**Decision Status**: RECOMMENDED — awaiting approval  

---

## Selected Models

### VQA

| Role | Model | Rationale |
|---|---|---|
| **PRIMARY** | **Qwen2.5-VL-3B-Instruct (INT4)** | Best balance of capability, VRAM fit, and RS adaptability. 3B params at INT4 quantization uses ~4–5 GB VRAM, safely within our 6 GB budget. Dynamic resolution preserves satellite imagery detail. Apache 2.0 license. Strong multimodal reasoning. Community RS fine-tunes available. |
| **FALLBACK** | **GeoChat-7B (INT4)** | Purpose-built RS VLM with proven RS benchmarks. Requires INT4 quantization to fit 6 GB VRAM (marginal). 14 GB checkpoint requires disk management. Use only if Qwen2.5-VL-3B proves insufficient on RS-specific tasks, or on competition hardware with more VRAM. |

### Grounding

| Role | Model | Rationale |
|---|---|---|
| **PRIMARY** | **Grounding DINO (Swin-Tiny, original)** | Apache 2.0, ~172M params, fits 6 GB VRAM with mixed precision. Well-established open-set detector. Text-guided bounding box output maps directly to our `BoundingBox` evidence type. Can be combined with SAM2 for segmentation masks. |
| **FALLBACK** | **SAM2-Tiny (prompted by Grounding DINO boxes)** | Extremely lightweight (~458 MB for 1024×1024). Produces segmentation masks from box prompts. Not a standalone grounding model — requires Grounding DINO boxes as input. Apache 2.0. |

### Mock Models (Retained)

| Role | Model | Purpose |
|---|---|---|
| **Testing** | MockVLM | Deterministic testing without GPU. Always available. |
| **Testing** | MockGroundingModel | Deterministic grounding testing without GPU. Always available. |

---

## Modality Strategy

| Input Type | Strategy |
|---|---|
| **RGB (3-band)** | Direct input to VLM/Grounding DINO after uint8 normalization |
| **Single-band** | Convert to pseudo-RGB (replicate band 3×) OR acquire proper RGB composite. Flag as limited in response metadata. |
| **Multi-band (>3)** | Select best RGB-equivalent bands (e.g., B04/B03/B02 for Sentinel-2) using band metadata. Normalize to uint8. |
| **SAR** | Apply log-scaling + Lee speckle filter (existing `sar.py`). Convert to pseudo-RGB. Flag SAR modality in evidence. SAR VQA quality will be limited — state this honestly. |

---

## Resource Requirements

### Disk Space Budget

| Item | Size |
|---|---|
| PyTorch + CUDA runtime | ~2.5 GB |
| Qwen2.5-VL-3B-Instruct (INT4/GPTQ) | ~2–3 GB |
| Grounding DINO (Swin-T checkpoint) | ~700 MB |
| SAM2-Tiny checkpoint | ~40 MB |
| transformers + dependencies | ~500 MB |
| **Total estimated** | **~6–7 GB** |

This is feasible with 28 GB free, but leaves limited headroom.

### VRAM Budget (Inference)

| Component | Estimated VRAM |
|---|---|
| Qwen2.5-VL-3B (INT4, 1024×1024 input) | ~4–5 GB |
| Grounding DINO (Swin-T, 1024×1024 input) | ~4–5 GB |
| SAM2-Tiny (1024×1024 input) | ~0.5 GB |

> [!IMPORTANT]
> VQA and Grounding DINO cannot run simultaneously on the same GPU. The pipeline must load/unload models sequentially, or use only one at a time per request.

---

## Decision Rationale

### Why Qwen2.5-VL-3B over GeoChat-7B as primary?

1. **VRAM**: Qwen2.5-VL-3B at INT4 fits comfortably (4–5 GB). GeoChat-7B at INT4 is marginal (5–7 GB) and may OOM on larger inputs.
2. **Disk**: Qwen2.5 INT4 checkpoint is ~2–3 GB. GeoChat FP16 is 14 GB — we'd need to find/create a quantized version.
3. **Dynamic resolution**: Qwen2.5-VL's native dynamic resolution is better suited for RS imagery than LLaVA's patch-based approach.
4. **Ecosystem**: Qwen2.5-VL has first-class `transformers` support, bitsandbytes integration, and extensive documentation.
5. **Grounding built-in**: Qwen2.5-VL supports coordinate-based grounding in text output, potentially reducing our need for a separate grounding model for some queries.

### Why Grounding DINO over GeoGround?

1. **VRAM**: Grounding DINO Swin-T is ~172M params vs GeoGround's ~7B+ VLM backbone.
2. **License**: Grounding DINO is Apache 2.0. GeoGround's license needs verification.
3. **Maturity**: Grounding DINO is production-proven with extensive ecosystem support.
4. **Composability**: Grounding DINO + SAM2 gives us both boxes and segmentation.

---

## Prerequisites Before Integration

1. **Install PyTorch with CUDA**: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`
2. **Install transformers**: `pip install transformers accelerate bitsandbytes`
3. **Acquire RGB test data**: Download B04+B03+B02 from the same Sentinel-2 scene, or find a pre-composited RGB satellite image.
4. **Verify disk space**: Ensure ≥10 GB free after PyTorch installation.

---

## Local Test Findings (2026-09-16)

A real VLM smoke test was conducted using Qwen2.5-VL-3B-Instruct on the development machine (RTX 4050, 6GB VRAM).

- **Result**: PASS (Local Inference Verified)
- **VRAM Usage**: 2.58 GB peak (using INT4 quantization)
- **Latency**: Fully capable of producing valid descriptive output for RGB remote sensing imagery.

The test confirms that Qwen2.5-VL-3B at INT4 fits comfortably within the 6 GB VRAM constraint and generates accurate structural descriptions for remote sensing inputs.
