import os
import torch
import time
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig

# Suppress symlink warning
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

print("Starting smoke test for Qwen2.5-VL-3B-Instruct...")
model_id = "Qwen/Qwen2.5-VL-3B-Instruct"

print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# Configure INT4 quantization
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4"
)

try:
    start_time = time.time()
    print("Loading processor...")
    processor = AutoProcessor.from_pretrained(model_id)
    
    print("Loading model in INT4...")
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_id,
        device_map="auto",
        quantization_config=quantization_config
    )
    load_time = time.time() - start_time
    
    print(f"Model loaded successfully in {load_time:.2f} seconds.")
    
    if torch.cuda.is_available():
        memory_allocated = torch.cuda.memory_allocated() / (1024 ** 3)
        print(f"VRAM Allocated: {memory_allocated:.2f} GB")
        
except Exception as e:
    print(f"Model loading failed: {e}")
