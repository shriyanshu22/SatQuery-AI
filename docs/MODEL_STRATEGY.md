# Model Strategy

## 1. Three-Tier Model System
To ensure development speed, CI/CD stability, and robust demonstrations, all models implement a strict protocol across three tiers:
1. **RealModel**: The actual PyTorch/Transformers model. Runs live inference. Requires GPU.
2. **CachedModelOutput**: Replays *genuine* pre-computed outputs from the RealModel based on deterministic input hashes. Crucial for demo mode on CPU-only machines.
3. **MockModel**: Deterministic stubs (hardcoded dummy data) used strictly for unit testing and CI pipelines.

## 2. Per-Capability Model Candidates

| Capability | Primary Candidate | Alternatives / Pros & Cons |
|------------|-------------------|----------------------------|
| VQA | Qwen2-VL-2B | Qwen2.5-VL-3B (better, heavier); BLIP-2 (faster, older); GeoChat (RS specific but hard to run). |
| Grounding | Grounding DINO + SAM | GeoGround (domain specific); RSVG-ZeroOV. DINO is robust for zero-shot. |
| Change Detection| Siamese CNN (ResNet) | Pixel Difference (baseline); ABLRCNet. |
| SAR Analysis | ResNet (grayscale) | Specialized SAR extractors (requires extensive fine-tuning). |

## 3. Protocol-Based Abstraction Design
```python
from typing import Protocol, Any
from core.evidence import Evidence

class VisionLanguageModel(Protocol):
    def infer(self, image: Any, prompt: str) -> Evidence:
        ...
```
*Design Rule*: The service layer calls `infer()`. It does not know if the model is Real, Cached, or Mock.

## 4. Hardware & GPU Requirements

| Model Tier | Minimum VRAM | Recommended VRAM | System RAM |
|------------|--------------|------------------|------------|
| Qwen2-VL-2B| 6 GB (quant) | 8 GB             | 16 GB      |
| Qwen2.5-VL | 8 GB (quant) | 12 GB            | 16 GB      |
| GrDINO+SAM | 6 GB         | 8 GB             | 16 GB      |
| Demo Mode  | 0 GB (CPU)   | 0 GB             | 8 GB       |

**CPU Fallback Strategy**: 
If PyTorch detects no CUDA, the system automatically switches to `CachedModelOutput` for bundled demo images, or throws a graceful `422 Unprocessable Entity` for novel images demanding live inference.

## 5. Download Sizes and Caching
- Qwen2-VL-2B: ~4-5 GB.
- Grounding DINO: ~1 GB.
- Cached Outputs DB: < 10 MB.
*All weights downloaded to `~/.cache/huggingface`.*

## 6. Licensing Review
- Qwen2-VL: Apache 2.0 / Qwen License (Permissive).
- Grounding DINO: Apache 2.0.
- SAM: Apache 2.0.
All choices are strictly compliant with open-source hackathon requirements.
