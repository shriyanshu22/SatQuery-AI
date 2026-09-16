# Model Research — SatQuery AI (SIH26)

**Date**: 2026-09-16  
**Phase**: Pre-Integration Research  
**Author**: Automated audit  

---

## 1. Hardware Audit

| Property | Value |
|---|---|
| **Operating System** | Windows 10 (Build 10.0.26200) |
| **CPU** | 13th Gen Intel Core i5-13450HX (10 cores / 16 threads, 2.4 GHz base) |
| **System RAM** | 16 GB |
| **GPU** | NVIDIA GeForce RTX 4050 Laptop GPU |
| **GPU VRAM** | 6141 MiB (~6 GB) |
| **CUDA Version** | 13.1 |
| **Driver** | 591.86 |
| **PyTorch** | **NOT INSTALLED** — must be installed before any model integration |
| **Python** | 3.11.0 |
| **Disk** | SK Hynix 512 GB NVMe — **28.2 GB free** |

### Hardware Constraints Summary

- **6 GB VRAM** is the hard ceiling. Models requiring >5.5 GB in practice will OOM.
- **28 GB free disk** is very tight — a single 7B FP16 checkpoint is ~14 GB. Quantized models (GPTQ/AWQ 4-bit) are typically 3–5 GB.
- **16 GB system RAM** allows CPU offloading for inference but with severe speed penalties.
- PyTorch + CUDA must be installed as a prerequisite.

### CUDA / PyTorch Test

```
python -c "import torch; print(torch.cuda.is_available())"
→ ModuleNotFoundError: No module named 'torch'
```

```
nvidia-smi
→ RTX 4050 Laptop GPU, 6141 MiB total, 0 MiB used, CUDA 13.1
```

**Action required**: Install PyTorch with CUDA support before any model integration.

---

## 2. VQA Model Research

### Candidate A: Qwen2.5-VL-3B (Instruct)

| Criterion | Assessment |
|---|---|
| **Model** | Qwen2.5-VL-3B-Instruct |
| **Repository** | [Qwen/Qwen2.5-VL-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct) |
| **Checkpoint** | `Qwen2.5-VL-3B-Instruct` (HF transformers compatible) |
| **License** | Apache 2.0 |
| **Parameters** | ~3B |
| **VRAM (FP16)** | ~6–8 GB |
| **VRAM (INT4)** | ~4–6 GB — **fits our 6 GB GPU** |
| **Quantization** | Supported via bitsandbytes (NF4), GPTQ, AWQ |
| **RS Training** | General-purpose, but community RS fine-tunes exist on HuggingFace |
| **VQA Capability** | Strong multimodal VQA; dynamic resolution preserves spatial detail |
| **Grounding** | Supports bounding box output in response text (coordinate-based) |
| **Input Format** | PIL Image / RGB tensor; dynamic resolution (no forced 224×224) |
| **Inference** | ~2–5 seconds per query on consumer GPU (quantized) |
| **Integration** | HuggingFace transformers, well-documented API |
| **Compatibility** | Requires RGB 3-channel input → adapter must convert single-band to pseudo-RGB |
| **Local Dev** | ✅ Feasible with INT4 quantization on RTX 4050 |
| **Competition** | ✅ Impressive demo quality; fast inference; small disk footprint |

**Evidence**: Qwen2.5-VL is documented as supporting edge deployment. RS-specific fine-tunes exist on HuggingFace. The dynamic resolution feature is critical for satellite imagery where forced resizing destroys spatial detail.

### Candidate B: GeoChat-7B

| Criterion | Assessment |
|---|---|
| **Model** | GeoChat-7B |
| **Repository** | [MBZUAI/geochat-7B](https://huggingface.co/MBZUAI/geochat-7B) |
| **Checkpoint** | `geochat-7B` (~14.2 GB FP16) |
| **License** | Apache 2.0 |
| **Parameters** | ~7B |
| **VRAM (FP16)** | ~14.2 GB — **does NOT fit** |
| **VRAM (INT4)** | ~5–7 GB — **marginal, may OOM with large images** |
| **Quantization** | Possible but not officially distributed as quantized |
| **RS Training** | ✅ **Purpose-built for remote sensing** — trained on 318K RS instruction pairs |
| **VQA Capability** | Strong RS-specific VQA, scene classification, image captioning |
| **Grounding** | ✅ Built-in visual grounding via coordinate text output |
| **Input Format** | High-resolution patch-level tokens (LLaVA architecture) |
| **Inference** | Slower than 3B models; memory-constrained on 6 GB |
| **Integration** | LLaVA-1.5 architecture, requires specific loading code |
| **Compatibility** | Expects RGB input; similar adapter requirements |
| **Local Dev** | ⚠️ Risky — INT4 quantization is mandatory, 14 GB checkpoint requires disk space |
| **Competition** | ✅ Domain credibility is very high — judges will recognize RS-specific training |

**Evidence**: GeoChat was the first RS-specific VLM to introduce visual grounding. Published research with benchmarks on RSVQA, NWPU-Caption. Trained on 3×A100 GPUs but quantized inference is documented. The 14 GB checkpoint is a storage concern with only 28 GB free.

### Candidate C: Qwen2-VL-2B (Instruct)

| Criterion | Assessment |
|---|---|
| **Model** | Qwen2-VL-2B-Instruct |
| **Parameters** | ~2B |
| **VRAM (FP16)** | ~5 GB — **fits** |
| **RS Training** | None (general-purpose) |
| **VQA** | Moderate quality; previous generation to Qwen2.5 |
| **Grounding** | Limited compared to 2.5 series |
| **Local Dev** | ✅ Very safe on 6 GB |
| **Competition** | ⚠️ Weaker answers; less impressive demo |

### Candidate D: SmolVLM-2B

| Criterion | Assessment |
|---|---|
| **Model** | SmolVLM (HuggingFace) |
| **Parameters** | ~2B |
| **VRAM** | ~3–4 GB — very safe |
| **RS Training** | None |
| **VQA** | Reasonable for simple queries |
| **Grounding** | Not specialized |
| **Local Dev** | ✅ |
| **Competition** | ⚠️ Generic; no RS domain credibility |

---

## 3. Grounding Model Research

### Candidate A: Grounding DINO (Original)

| Criterion | Assessment |
|---|---|
| **Model** | Grounding DINO (Swin-Tiny + BERT-Base) |
| **Repository** | [IDEA-Research/GroundingDINO](https://github.com/IDEA-Research/GroundingDINO) |
| **License** | Apache 2.0 |
| **Parameters** | ~172M (Swin-T variant) |
| **VRAM** | ~6.4 GB baseline, spikes possible — **tight but feasible** |
| **RS Performance** | Designed for natural images; sub-optimal out-of-box for RS. LoRA adaptation recommended. |
| **Input** | RGB image + text prompt |
| **Output** | Bounding boxes with confidence scores |
| **Segmentation** | No (but combinable with SAM for masks) |
| **Integration** | HuggingFace transformers support; well-documented |
| **Local Dev** | ✅ Feasible with mixed precision |

**Evidence**: Grounding DINO is the standard open-set detector. RS practitioners commonly use it as a teacher model or with LoRA adaptation. VRAM can spike during inference on high-resolution inputs — tiling may be required for 1024×1024+ images.

### Candidate B: SAM2 (Segment Anything Model 2)

| Criterion | Assessment |
|---|---|
| **Model** | SAM 2 (Tiny/Small/Base-plus/Large) |
| **License** | Apache 2.0 |
| **Parameters** | Tiny: ~10M, Large: ~300M+ |
| **VRAM** | Tiny at 1024×1024: ~458 MB — **very safe** |
| **RS Performance** | Designed for natural images; reasonable for salient object segmentation in RS with prompts |
| **Input** | Image + point/box/mask prompts |
| **Output** | Segmentation masks |
| **Bounding Boxes** | No (prompt-based, not text-guided) |
| **Integration** | Straightforward; HuggingFace and official repo |
| **Local Dev** | ✅ Very lightweight |

**Note**: SAM2 is a segmentation model, not a text-guided detector. It complements Grounding DINO (Grounded SAM pipeline: GDINO detects → SAM segments).

### Candidate C: GeoGround

| Criterion | Assessment |
|---|---|
| **Model** | GeoGround |
| **Repository** | [zytx121/GeoGround](https://github.com/zytx121/GeoGround) |
| **License** | Research/academic (check before competition use) |
| **Parameters** | VLM-based (likely 7B+ given LLaVA architecture) |
| **VRAM** | Likely >14 GB FP16 — **does NOT fit without quantization** |
| **RS Performance** | ✅ Purpose-built for RS visual grounding (HBB, OBB, masks) |
| **Input** | Image + text referring expression |
| **Output** | Bounding boxes (HBB/OBB) and segmentation masks |
| **Integration** | Research code; may require custom integration |
| **Local Dev** | ⚠️ Risky — likely too large for 6 GB VRAM |

**Evidence**: GeoGround is the most RS-specialized grounding model available. It supports HBB, OBB, and masks in a unified framework. However, it is a full VLM (~7B+) which exceeds our VRAM budget without aggressive quantization. License status needs verification before competition use.

---

## 4. B02.tif Data Format Analysis

### File Properties

| Property | Value |
|---|---|
| **Width** | 1024 |
| **Height** | 1024 |
| **Bands** | 1 (single-band) |
| **Dtype** | uint16 |
| **CRS** | EPSG:32633 (UTM Zone 33N) |
| **Resolution** | 10m × 10m |
| **Bounds** | 377720–387960 E, 5340230–5350470 N |
| **Nodata** | 0.0 |
| **Source** | Copernicus Sentinel-2 L2A (Band B02 = Blue, 490 nm) |
| **Acquisition** | 2023-09-07T10:00:31.024000Z |
| **MGRS Tile** | 33UUP |
| **Value Range** | 340–18496 (mean 1552.9) |
| **Unique Values** | 2298 distinct values |
| **Zero Pixels** | 0 (no nodata present) |
| **Color Interp** | Gray |

### Suitability for Real VQA

**B02.tif is NOT directly suitable for real VQA.**

Reasons:
1. **Single-band**: VLMs expect 3-channel RGB input. A single blue band provides no color information for scene interpretation.
2. **uint16 reflectance values**: VLMs expect uint8 [0-255] or float32 [0-1] normalized images. Raw Sentinel-2 reflectance values (340–18496) must be normalized.
3. **No true color**: Meaningful visual questions ("Is there a building?") require at minimum an RGB composite (B04-Red, B03-Green, B02-Blue).

### Required Transformations for Model Input

| Step | Original Data | Model Input |
|---|---|---|
| Band composition | 1 band (B02 Blue) | 3 bands (RGB composite from B04, B03, B02) |
| Dtype conversion | uint16 [340–18496] | uint8 [0–255] or float32 [0–1] |
| Normalization | Raw reflectance | Percentile-clipped, min-max scaled |
| Channel order | (C, H, W) | Model-specific: some expect (H, W, C) |
| Resizing | 1024×1024 | Model-specific (many accept native resolution) |

### What We Need Next

For real VQA/grounding testing, we need:
1. **A true-color RGB composite** — either B04+B03+B02 from the same Sentinel-2 scene, or a pre-composited RGB GeoTIFF.
2. **A scene with identifiable features** — buildings, roads, water bodies, vegetation boundaries — to produce meaningful VQA responses.
3. **Optionally**: A very-high-resolution (VHR) aerial/satellite image (RGB, <1m resolution) for grounding tasks where individual objects are visible.

---

## 5. License Summary

| Model | License | Competition Safe? |
|---|---|---|
| Qwen2.5-VL-3B-Instruct | Apache 2.0 | ✅ Yes |
| GeoChat-7B | Apache 2.0 | ✅ Yes |
| Grounding DINO (original) | Apache 2.0 | ✅ Yes |
| SAM2 | Apache 2.0 | ✅ Yes |
| GeoGround | Research (verify) | ⚠️ Verify before use |
| Qwen2-VL-2B | Apache 2.0 | ✅ Yes |

---

## 6. Risk Register Additions

| Risk | Impact | Mitigation |
|---|---|---|
| 6 GB VRAM OOM with quantized 3B model | High | Monitor VRAM; reduce `max_pixels`; implement tiling |
| 28 GB free disk insufficient for model + data | High | Clean disk; use quantized checkpoints only; avoid storing multiple model versions |
| PyTorch not installed | Blocking | Install `torch` with CUDA support as prerequisite |
| Single-band B02.tif inadequate for VQA demo | Medium | Acquire RGB composite or download B04+B03+B02 bands |
| GeoChat-7B too large for local dev | Medium | Use Qwen2.5-VL-3B as primary; reserve GeoChat for cloud/competition hardware |
| Grounding DINO VRAM spikes on large images | Medium | Implement tiling; use mixed precision |
