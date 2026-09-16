# Real Model Integration Plan — SatQuery AI (SIH26)

**Date**: 2026-09-16  
**Status**: PLAN ONLY — no implementation yet  
**Prerequisite**: Model selection approved, PyTorch installed  

---

## Overview

This document describes the changes required to integrate real ML models into the SatQuery AI backend, replacing MockVLM and MockGroundingModel with Qwen2.5-VL-3B and Grounding DINO respectively.

The three-tier model architecture (RealModel / MockModel / CachedModelOutput) is already defined in the project rules. This plan implements `RealModel` for VQA and Grounding.

---

## Phase A: Prerequisites

### A1. Install PyTorch + CUDA

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Verify:
```python
import torch
print(torch.cuda.is_available())  # Must be True
print(torch.cuda.get_device_name(0))  # RTX 4050
```

### A2. Install Model Dependencies

```bash
pip install transformers accelerate bitsandbytes
pip install qwen-vl-utils  # Qwen2.5-VL specific utilities
```

### A3. Acquire RGB Test Data

Download B04 (Red), B03 (Green), B02 (Blue) bands from the same Sentinel-2 scene (MGRS tile 33UUP, 2023-09-07) and create a composite, OR download a pre-composited RGB satellite image.

---

## Phase B: Model Adapter Enhancements

### Current State

The existing adapter pipeline (`backend/preprocessing/adapters.py`) provides:
- `VLMAdapter`: Converts RSDataObject to uint8, takes first 3 bands
- `GroundingAdapter`: Converts to uint8

### Required Changes

#### B1. New `Qwen25VLAdapter` (in `backend/preprocessing/adapters.py`)

| Step | Current | Required |
|---|---|---|
| **Band selection** | Naive first-3 | Intelligent: use B04/B03/B02 if Sentinel-2; fallback to first-3; replicate if single-band |
| **Dtype** | uint8 via `to_uint8()` | float32 [0, 1] normalized OR PIL Image depending on model processor |
| **Normalization** | Simple minmax | Percentile-clipped (2nd–98th) to handle outliers in RS data |
| **Channel order** | (C, H, W) | PIL Image (H, W, C) for Qwen processor |
| **Resize** | None | Controlled via `min_pixels` / `max_pixels` in Qwen processor config |
| **Device** | CPU numpy | CPU (processor handles device placement) |
| **Output type** | numpy array | PIL.Image.Image |

```python
class Qwen25VLAdapter(ModelAdapter):
    """Adapter for Qwen2.5-VL models."""
    
    def __init__(self, max_pixels: int = 1024 * 1024):
        self.max_pixels = max_pixels
    
    def adapt(self, rs_data: RSDataObject) -> PIL.Image.Image:
        # 1. Select RGB bands intelligently
        data = self._select_rgb_bands(rs_data)
        # 2. Normalize to [0, 255] uint8 with percentile clipping
        data = self._normalize_for_display(data)
        # 3. Convert (C, H, W) → (H, W, C)
        data = np.transpose(data, (1, 2, 0))
        # 4. Return as PIL Image
        return Image.fromarray(data)
```

#### B2. New `GroundingDINOAdapter`

| Step | Required |
|---|---|
| **Band selection** | Same RGB logic as VLM adapter |
| **Normalization** | ImageNet-style mean/std normalization (GDINO expects this) |
| **Resize** | Model processor handles; typically 800×1333 max |
| **Output** | PIL Image (GDINO processor handles tensor conversion) |

#### B3. Single-Band Handling Strategy

```python
def _select_rgb_bands(self, rs_data: RSDataObject) -> np.ndarray:
    """Intelligently select or construct RGB bands."""
    data = rs_data.data  # (C, H, W)
    
    if data.shape[0] >= 3:
        # Multi-band: try Sentinel-2 band mapping, else first 3
        return data[:3]
    elif data.shape[0] == 1:
        # Single band: replicate to pseudo-RGB
        return np.repeat(data, 3, axis=0)
    else:
        raise PreprocessingError(f"Unexpected band count: {data.shape[0]}")
```

---

## Phase C: Real VQA Model Implementation

### C1. New file: `backend/models/real_vlm.py`

```python
class Qwen25VLModel(BaseModel, VLMProtocol):
    """Real Qwen2.5-VL-3B model for VQA."""
    
    def __init__(self, 
                 checkpoint: str = "Qwen/Qwen2.5-VL-3B-Instruct",
                 quantize: bool = True,
                 device: str = "cuda"):
        super().__init__("qwen25-vl-3b")
        self.checkpoint = checkpoint
        self.quantize = quantize
        self.device = device
        self._model = None
        self._processor = None
    
    def load(self) -> None:
        from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
        
        load_kwargs = {"device_map": "auto"}
        if self.quantize:
            from transformers import BitsAndBytesConfig
            load_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4"
            )
        
        self._processor = AutoProcessor.from_pretrained(self.checkpoint)
        self._model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.checkpoint, **load_kwargs
        )
        self._loaded = True
    
    def predict(self, image: np.ndarray, prompt: str, **kwargs) -> VLMResult:
        # image is already adapted to PIL by the adapter
        messages = [{"role": "user", "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": prompt}
        ]}]
        text = self._processor.apply_chat_template(messages, ...)
        inputs = self._processor(text=text, images=[image], return_tensors="pt")
        inputs = inputs.to(self._model.device)
        
        output_ids = self._model.generate(**inputs, max_new_tokens=256)
        answer = self._processor.batch_decode(output_ids, ...)
        
        return VLMResult(answer=answer, evidence=[], confidence=..., raw_output=...)
```

### C2. Protocol Compatibility

The existing `VLMProtocol` expects `predict(image: np.ndarray, prompt: str)`. 

**Decision needed**: The real model adapter returns PIL Images, not numpy arrays. Options:
1. Change protocol signature to `image: Any` (breaks type safety)
2. Keep numpy in protocol; do PIL conversion inside the model's `predict()` method
3. Pass `RSDataObject` instead of raw array (architectural change)

**Recommendation**: Option 2 — keep the protocol signature but accept that the adapter output is used internally. The `VQAService` already calls `adapter.adapt()` separately and passes the result to `model.predict()`.

---

## Phase D: Real Grounding Model Implementation

### D1. New file: `backend/models/real_grounding.py`

```python
class GroundingDINOModel(BaseModel, GroundingProtocol):
    """Real Grounding DINO model for object detection."""
    
    def __init__(self,
                 checkpoint: str = "IDEA-Research/grounding-dino-tiny",
                 device: str = "cuda"):
        super().__init__("grounding-dino")
        self.checkpoint = checkpoint
        self.device = device
    
    def load(self) -> None:
        from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
        self._processor = AutoProcessor.from_pretrained(self.checkpoint)
        self._model = AutoModelForZeroShotObjectDetection.from_pretrained(
            self.checkpoint
        ).to(self.device)
        self._loaded = True
    
    def ground(self, image: np.ndarray, text_query: str, **kwargs) -> GroundingResult:
        inputs = self._processor(images=image, text=text_query, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self._model(**inputs)
        
        # Post-process to get boxes
        results = self._processor.post_process_grounded_object_detection(
            outputs, inputs["input_ids"], threshold=0.3, ...
        )
        
        boxes = [BoundingBox(x=..., y=..., w=..., h=..., label=..., confidence=...)
                 for box, score, label in zip(...)]
        
        return GroundingResult(boxes=boxes, evidence=[], confidence=..., raw_output=...)
```

---

## Phase E: Configuration and Model Selection

### E1. Update `backend/core/config.py`

Add model configuration:

```python
class ModelConfig(BaseModel):
    vqa_backend: Literal["mock", "qwen25vl", "geochat"] = "mock"
    grounding_backend: Literal["mock", "grounding_dino"] = "mock"
    vqa_checkpoint: str = "Qwen/Qwen2.5-VL-3B-Instruct"
    grounding_checkpoint: str = "IDEA-Research/grounding-dino-tiny"
    quantize: bool = True
    device: str = "cuda"
    max_image_pixels: int = 1024 * 1024
```

### E2. Model Factory

Update the route initialization to select between mock and real models based on configuration:

```python
def get_vqa_model(config: ModelConfig) -> VLMProtocol:
    if config.vqa_backend == "mock":
        return MockVLM()
    elif config.vqa_backend == "qwen25vl":
        return Qwen25VLModel(checkpoint=config.vqa_checkpoint, quantize=config.quantize)
```

---

## Phase F: Tiling for Large Images

### Problem

Both Qwen2.5-VL and Grounding DINO have practical limits on input resolution due to VRAM. Sentinel-2 tiles can be very large.

### Strategy

1. **VQA**: Use Qwen2.5-VL's built-in `min_pixels`/`max_pixels` to control resolution. The processor downsamples internally.
2. **Grounding**: For images >1024×1024, use the existing `tiling.py` to split into overlapping tiles, run detection per tile, then merge boxes with NMS (Non-Maximum Suppression).

### Required New Code

```python
# backend/preprocessing/inference_tiling.py
def tile_and_detect(model, image, query, tile_size=1024, overlap=128):
    """Run detection on tiles and merge results."""
    tiles = tile_image(image, tile_size, overlap)
    all_boxes = []
    for tile, offset in tiles:
        result = model.ground(tile, query)
        all_boxes.extend(offset_boxes(result.boxes, offset))
    return nms_merge(all_boxes)
```

---

## Phase G: Testing Plan

### G1. Unit Tests (no GPU required)

- Verify adapter produces correct output shapes and types
- Verify model factory returns correct model type
- Mock model tests continue to pass unchanged
- Config parsing tests for new model settings

### G2. Integration Tests (GPU required)

- Load Qwen2.5-VL-3B INT4 on RTX 4050
- Verify VRAM stays under 5.5 GB
- Run VQA on RGB satellite image
- Verify answer is non-empty and relevant
- Load Grounding DINO on RTX 4050
- Run detection on satellite image with text prompt
- Verify bounding boxes are within image bounds

### G3. End-to-End Tests

- Upload real RGB satellite image via API
- Query via `/api/v1/query`
- Verify response uses real model name (not "mock-vlm")
- Verify confidence comes from real model logits
- Verify evidence contains real spatial metadata

---

## Files to Create/Modify

| Action | File | Description |
|---|---|---|
| **NEW** | `backend/models/real_vlm.py` | Qwen2.5-VL-3B wrapper implementing VLMProtocol |
| **NEW** | `backend/models/real_grounding.py` | Grounding DINO wrapper implementing GroundingProtocol |
| **MODIFY** | `backend/preprocessing/adapters.py` | Add Qwen25VLAdapter and GroundingDINOAdapter |
| **MODIFY** | `backend/core/config.py` | Add ModelConfig with backend selection |
| **MODIFY** | `backend/api/routes.py` | Use config-driven model factory |
| **NEW** | `backend/preprocessing/inference_tiling.py` | Tile-based inference for large images |
| **NEW** | `backend/tests/test_real_models.py` | Integration tests (GPU-gated) |
| **MODIFY** | `requirements.txt` or `pyproject.toml` | Add torch, transformers, accelerate, bitsandbytes |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Qwen2.5-VL-3B INT4 OOMs on 1024×1024 | Medium | High | Reduce `max_pixels`; fallback to 512×512 |
| GDINO VRAM spike on detection | Medium | Medium | Use mixed precision; tile large images |
| Model download fails during competition | Low | Critical | Pre-download and cache all checkpoints |
| Real model produces hallucinated answers for RS | High | Medium | Validate answers; include confidence; state model limitations in evidence |
| PyTorch/CUDA version mismatch | Low | Blocking | Pin versions in requirements |
| Grounding DINO poor on aerial/satellite objects | Medium | Medium | LoRA fine-tune on DOTA/VRSBench if time permits; otherwise honest confidence reporting |
