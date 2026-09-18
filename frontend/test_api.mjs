import fs from 'fs';

async function runTests() {
    console.log("=== Testing Backend Endpoints ===");
    
    // 1. Upload a dummy image to verify backend returns a UUID
    console.log("1. Uploading image to /api/v1/upload...");
    const form = new FormData();
    const dummyFile = new Blob(["dummy data for testing"], { type: "image/tiff" });
    form.append("file", dummyFile, "test_image.tif");
    
    const uploadRes = await fetch("http://localhost:8000/api/v1/upload", {
        method: "POST",
        body: form
    });
    
    const uploadData = await uploadRes.json();
    console.log("-> Upload Response Image ID (UUID):", uploadData.image_id);
    
    const imageId = uploadData.image_id;

    async function submitQuery(query) {
        console.log(`\n-> Submitting query: "${query}" with image_id: ${imageId}`);
        const queryRes = await fetch("http://localhost:8000/api/v1/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: query,
                image_ids: [imageId],
                include_evidence: true,
                include_trace: true
            })
        });
        
        const queryData = await queryRes.json();
        if (queryData.task_id) {
            let status = "processing";
            while (status !== "completed" && status !== "failed") {
                await new Promise(r => setTimeout(r, 1000));
                const statRes = await fetch(`http://localhost:8000/api/v1/status/${queryData.task_id}`);
                const statData = await statRes.json();
                status = statData.status;
            }
            if (status === "completed") {
                const resRes = await fetch(`http://localhost:8000/api/v1/result/${queryData.task_id}`);
                const resData = await resRes.json();
                console.log("-> Final Answer:", resData.result.answer);
                console.log("-> Confidence:", resData.result.confidence.score);
                // Check if any boxes
                const boxes = resData.result.evidence.filter(e => e.type === "bounding_box");
                if (boxes.length > 0) {
                    console.log(`-> Found ${boxes.length} bounding box(es)`);
                    boxes.forEach(b => {
                        console.log(`   Box label: ${b.data.label}`);
                    });
                }
            } else {
                console.log("-> Task failed.");
            }
        } else {
            console.log("-> Query Error:", queryData);
        }
    }

    // 2. Submit VQA queries
    console.log("\n--- Testing VQA ---");
    await submitQuery("What objects are visible in this image?");
    await submitQuery("Is there a basketball court?");

    // 3. Submit Grounding queries
    console.log("\n--- Testing Grounding ---");
    await submitQuery("Where are the buildings?");
    await submitQuery("Locate the basketball court.");
    await submitQuery("Locate the road.");

}

runTests().catch(console.error);
