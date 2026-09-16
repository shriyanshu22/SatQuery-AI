# Real VLM Smoke Test

## Machine Specifications
- **GPU**: NVIDIA GeForce RTX 4050 Laptop GPU
- **VRAM**: 6 GB (6141 MiB)
- **RAM**: 16 GB
- **CPU**: Intel i5-13450HX
- **OS**: Windows

## Environment
- **NVIDIA Driver**: 591.86
- **CUDA**: 12.6
- **PyTorch Version**: 2.14.0+cu126
- **Transformers Version**: 5.17.0
- **BitsAndBytes**: 0.50.2

## Model Configuration
- **Model Checkpoint**: Qwen/Qwen2.5-VL-3B-Instruct
- **Quantization/Precision**: INT4 (nf4 via bitsandbytes)
- **Model Load Status**: LOADED successfully

## Test Details
- **Test Image**: `data/demo/image.jpg` (RGB Remote-Sensing)
- **Input Dimensions**: 800x800x3 (uint8)
- **Prompt**: "What objects or land-cover features are visible in this image?"

## Inference Results
- **Result Status**: PASS
- **VRAM Peak**: 2.58 GB
- **Latency**: 1406.17 seconds (Note: Includes initial ~22 minutes of HF Hub download time; subsequent passes will be faster).
- **Model Output**:
  > The image shows an aerial view of a residential area with several key features:
  > 
  > 1. **Houses**: There are multiple houses visible, each with different roof designs and sizes.
  > 2. **Roofs**: The roofs of the houses vary in color and design, indicating different materials and styles.
  > 3. **Yard Areas**: Each house has a yard area, which appears to be landscaped with grass and possibly some trees or shrubs.
  > 4. **Driveways**: Several driveways are visible, leading up to the houses.
  > 5. **Street**: A street runs parallel to the houses, with a sidewalk on one side.
  > 6

## Errors and Limitations
- **Errors**: `qwen_vl_utils` and `torch.utils.flop_counter.py` threw a harmless warning about missing Triton on Windows (`triton not found; flop counting will not work for triton kernels`). 
- **Limitations**: Max tokens output was limited resulting in truncation at "6". VRAM is heavily constrained; only 6 GB available. Running concurrent VLM queries will likely trigger Out-of-Memory (OOM) errors. We must maintain INT4 inference for stability.

## WARM INFERENCE BENCHMARK

- **Model Load Time**: 26.09 seconds
- **First Inference (Cold Start)**: 6.52 seconds
- **Second Inference (Warm)**: 4.93 seconds
- **Third Inference (Warm)**: 4.74 seconds
- **Average Warm Inference**: 4.84 seconds
- **VRAM Observed**: 2.58 GB

*(Note: The earlier 1406.17 second result included the model checkpoint download from HuggingFace and is NOT representative of normal inference latency. As measured above, warm inference generates full responses in under 5 seconds, which supports rapid inference claims for this hardware profile.)*

