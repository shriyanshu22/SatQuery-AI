# Evaluation Framework

## 1. Objective
To rigorously and honestly quantify the performance of SatQuery AI across all multimodal capabilities, ensuring continuous improvement and preventing regressions.

## 2. Per-Capability Metrics

### 2.1 Visual Question Answering (VQA)
- **Exact Match Accuracy**: Strict string matching.
- **Relaxed Accuracy**: Semantic similarity matching (using a lightweight sentence transformer or BLEU/ROUGE).
- **Per-Category Breakdown**: Accuracy grouped by question type (e.g., counting, presence, land-cover classification).

### 2.2 Text-Guided Grounding
- **Intersection over Union (IoU)**: Overlap between predicted bounding boxes and ground truth.
- **mean Average Precision (mAP)**: At standard IoU thresholds (0.5, 0.75).
- **Precision@IoU**: Percentage of predictions that meet an IoU threshold.

### 2.3 Bi-Temporal Change Detection
- **F1 Score**: Harmonic mean of precision and recall for changed pixels.
- **IoU (Change class)**: Intersection of predicted change vs true change.
- **Precision / Recall**: To analyze over-prediction vs under-prediction.

### 2.4 Cross-Modal Analysis
- **Agreement Accuracy**: How often the system correctly identifies agreement or disagreement between Optical and SAR data compared to human annotation.

### 2.5 Agent Routing
- **Routing Accuracy**: Percentage of queries routed to the correct capability.
- **Confusion Matrix**: Identifying which intents are commonly misclassified.

### 2.6 Input Validation & Security
- **False Positive Rate**: Valid files rejected.
- **False Negative Rate**: Corrupt/malicious files accepted.

## 3. Benchmark Datasets
- **VQA**: Subset of RSVQA (Test split).
- **Grounding**: Subset of VRSBench.
- **Change Detection**: LEVIR-CD test set.
- All evaluation subsets are stored in `tests/data/benchmarks/`.

## 4. Evaluation Runner Design
- **Script**: `scripts/evaluate.py`.
- **Mode**: Runs independently from the API to avoid HTTP overhead during pure model evaluation.
- **Pipeline**: Loads dataset -> Injects into `ModelAdapter` -> Computes metrics -> Saves to JSON.

## 5. Results Storage Format
Results are saved to `docs/evaluations/results_{timestamp}.json` with the schema:
```json
{
  "timestamp": "2026-09-14T10:00:00Z",
  "model_version": "qwen2-vl-lora-v1",
  "metrics": {
    "vqa_accuracy": 0.78,
    "vqa_relaxed": 0.85,
    "grounding_map_50": 0.62
  }
}
```

## 6. Comparison Methodology
- Benchmarks are run before and after applying fine-tuning (LoRA) or model swaps.
- CI pipelines can trigger smaller 'smoke tests' to ensure no catastrophic degradation.

## 7. Honesty Policy
**CRITICAL**: The system will never fabricate benchmark results. If a model performs poorly (e.g., 20% accuracy), it will be reported exactly as 20%. The goal of the hackathon is solving hard problems, not hiding them.
