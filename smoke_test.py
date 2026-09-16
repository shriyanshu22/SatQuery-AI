import time
import torch
import numpy as np
from PIL import Image
from backend.models.qwen_vlm import QwenVLM

def run_smoke_test():
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        
    print("\n--- Loading Image ---")
    image_path = "data/demo/image.jpg"
    try:
        pil_image = Image.open(image_path).convert("RGB")
        image_np = np.array(pil_image)
        print(f"Image loaded: {image_path}, shape: {image_np.shape}, dtype: {image_np.dtype}")
    except Exception as e:
        print(f"Failed to load image: {e}")
        return

    print("\n--- Initializing VLM ---")
    vlm = QwenVLM(model_id="Qwen/Qwen2.5-VL-3B-Instruct")
    
    print("\n--- Running Inference ---")
    prompt = "What objects or land-cover features are visible in this image?"
    
    start_time = time.time()
    try:
        result = vlm.predict(image=image_np, prompt=prompt, max_tokens=128)
        end_time = time.time()
        
        print("\n=== INFERENCE RESULT ===")
        print(result.answer)
        print("========================")
        print(f"Latency: {end_time - start_time:.2f} seconds")
        
        if torch.cuda.is_available():
            peak_memory = torch.cuda.max_memory_allocated(0) / (1024 ** 3)
            print(f"Peak VRAM used: {peak_memory:.2f} GB")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nInference failed: {e}")

if __name__ == "__main__":
    run_smoke_test()
