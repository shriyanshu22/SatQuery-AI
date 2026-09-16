import time
import torch
import numpy as np
from PIL import Image
from backend.models.qwen_vlm import QwenVLM

def run_warm_inference_benchmark():
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        
    image_path = "data/demo/image.jpg"
    pil_image = Image.open(image_path).convert("RGB")
    image_np = np.array(pil_image)
    
    print("\n--- Measuring Model Load Time ---")
    load_start = time.time()
    vlm = QwenVLM(model_id="Qwen/Qwen2.5-VL-3B-Instruct")
    vlm._load_model()
    load_end = time.time()
    load_time = load_end - load_start
    print(f"Model Load Time: {load_time:.2f} seconds")
    
    prompt = "What objects are visible in this image?"
    # Use max_tokens=1024 to avoid truncation
    max_tokens = 1024
    
    print("\n--- FIRST INFERENCE (Cold Start) ---")
    inf1_start = time.time()
    result1 = vlm.predict(image=image_np, prompt=prompt, max_tokens=max_tokens)
    inf1_end = time.time()
    inf1_time = inf1_end - inf1_start
    print(f"First Inference: {inf1_time:.2f} seconds")
    
    print("\n--- SECOND INFERENCE (Warm) ---")
    inf2_start = time.time()
    result2 = vlm.predict(image=image_np, prompt=prompt, max_tokens=max_tokens)
    inf2_end = time.time()
    inf2_time = inf2_end - inf2_start
    print(f"Second Inference: {inf2_time:.2f} seconds")

    print("\n--- THIRD INFERENCE (Warm) ---")
    inf3_start = time.time()
    result3 = vlm.predict(image=image_np, prompt=prompt, max_tokens=max_tokens)
    inf3_end = time.time()
    inf3_time = inf3_end - inf3_start
    print(f"Third Inference: {inf3_time:.2f} seconds")
    
    warm_avg = (inf2_time + inf3_time) / 2
    
    print("\n=== BENCHMARK REPORT ===")
    print(f"MODEL LOAD TIME: {load_time:.2f} seconds")
    print(f"FIRST INFERENCE: {inf1_time:.2f} seconds")
    print(f"SECOND INFERENCE: {inf2_time:.2f} seconds")
    print(f"THIRD INFERENCE: {inf3_time:.2f} seconds")
    print(f"AVERAGE WARM INFERENCE: {warm_avg:.2f} seconds")
    
    if torch.cuda.is_available():
        peak_memory = torch.cuda.max_memory_allocated(0) / (1024 ** 3)
        print(f"VRAM: {peak_memory:.2f} GB")
        
    print("\nMODEL OUTPUT:")
    print(result3.answer)
    
    # Simple truncation heuristic checking if it ended abruptly
    truncated = "YES" if len(result3.answer) > 0 and result3.answer[-1] not in ['.', '!', '?'] and len(result3.answer.split()) > max_tokens - 10 else "NO"
    print(f"TRUNCATED: {truncated}")

if __name__ == "__main__":
    run_warm_inference_benchmark()
