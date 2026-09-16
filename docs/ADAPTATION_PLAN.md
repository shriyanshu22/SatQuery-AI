# Remote-Sensing Model Adaptation Plan

## 1. Why Adaptation is Necessary
Vision-Language Models (VLMs) like Qwen2-VL are primarily trained on natural images (photos, internet datasets). Satellite imagery presents a massive domain gap:
- Top-down orthographic perspective.
- Diverse sensor modalities (SAR, Multispectral).
- Tiny objects (vehicles, buildings) relative to image size.
- Lack of standard RGB color correlation in false-color composites.

## 2. Datasets Under Investigation
| Dataset | Size | Target Task | Modality |
|---------|------|-------------|----------|
| **VRSBench** | ~10k QA pairs | VQA, Grounding | Optical |
| **RSVQA** | ~100k QA pairs | VQA | Optical |
| **LEVIR-CD** | ~600 pairs | Change Detection | Optical |
| **SEN1-2** | ~280k pairs | SAR-Optical translation| SAR/Optical |
| **BigEarthNet**| ~590k patches | Classification | Sentinel-1/2 |

## 3. Adaptation Approach (LoRA/PEFT)
Full fine-tuning of a 2B/3B model is computationally prohibitive for a hackathon. We will use **Low-Rank Adaptation (LoRA)** via the PEFT library.
- **Layers Targeted**: Attention weights (Q, K, V).
- **Rank (r)**: 16 or 32.
- **Precision**: 4-bit or 8-bit quantization (QLoRA) to fit training on a single 12GB/16GB GPU.

## 4. Adaptation Pipeline Design
1. **Data Prep**: Convert RSVQA/VRSBench to standard multi-turn conversation format (ShareGPT or similar).
2. **Training**: Use Hugging Face `TRL` (SFTTrainer) or `LLaMA-Factory`.
3. **Evaluation**: Benchmark against the baseline model (zero-shot).
4. **Deployment**: Load base model and dynamically load the LoRA adapter in `ModelAdapter`.

## 5. Expected Experiments
- **Experiment A**: Zero-shot Qwen2-VL on RSVQA test set.
- **Experiment B**: QLoRA fine-tuned Qwen2-VL on RSVQA train set.
- **Goal**: Demonstrate a measurable increase (>10%) in domain-specific accuracy.

## 6. Compute & Reproducibility Requirements
- Training script provided in `scripts/train_lora.py`.
- Must be runnable on a single RTX 3060/4090 or Google Colab T4/A100.
- All hyperparameters documented.

## 7. Honesty Policy / Success Criteria
- **Crucial Rule**: We will NOT claim the model is fine-tuned unless we have actually executed the training pipeline and can produce the adapter weights.
- "Successful adaptation" means the pipeline runs end-to-end and metrics improve, not that it beats state-of-the-art closed models.
