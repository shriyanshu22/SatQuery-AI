import httpx
import time

def run_tests():
    print("=== Testing Backend Endpoints ===")
    
    # 1. Upload
    print("1. Uploading image to /api/v1/upload...")
    with open("data/demo/image.jpg", "rb") as f:
        files = {"file": ("image.jpg", f, "image/jpeg")}
        upload_res = httpx.post("http://localhost:8000/api/v1/upload", files=files)
    
    upload_data = upload_res.json()
    image_id = upload_data.get("image_id")
    print(f"-> Upload Response Image ID (UUID): {image_id}")
    
    if not image_id:
        print("Failed to get image_id")
        return

    def submit_query(query):
        print(f"\n-> Submitting query: '{query}' with image_id: {image_id}")
        query_res = httpx.post("http://localhost:8000/api/v1/query", json={
            "query": query,
            "image_ids": [image_id],
            "include_evidence": True,
            "include_trace": True
        })
        
        query_data = query_res.json()
        task_id = query_data.get("task_id")
        if task_id:
            status = "processing"
            while status not in ["completed", "failed"]:
                time.sleep(1)
                stat_res = httpx.get(f"http://localhost:8000/api/v1/status/{task_id}")
                status = stat_res.json().get("status")
                
            if status == "completed":
                res_res = httpx.get(f"http://localhost:8000/api/v1/result/{task_id}")
                res_data = res_res.json().get("result", {})
                print(f"-> Final Answer: {res_data.get('answer')}")
                print(f"-> Confidence: {res_data.get('confidence', {}).get('score')}")
                boxes = [e for e in res_data.get('evidence', []) if e.get('type') == 'bounding_box']
                if boxes:
                    print(f"-> Found {len(boxes)} bounding box(es)")
                    for b in boxes:
                        print(f"   Box label: {b.get('data', {}).get('label')}")
            else:
                print("-> Task failed.")
        else:
            print("-> Query Error:", query_data)

    print("\n--- Testing VQA ---")
    submit_query("What objects are visible in this image?")
    submit_query("Is there a basketball court?")

    print("\n--- Testing Grounding ---")
    submit_query("Where are the buildings?")
    submit_query("Locate the basketball court.")
    submit_query("Locate the road.")

if __name__ == "__main__":
    run_tests()
