# Risk Register

| ID | Risk | Severity | Likelihood | Impact | Mitigation | Status | Category |
|---|---|---|---|---|---|---|---|
| RSK-01 | **GPU Availability** | High | High | Cannot run live inferences on dev laptops. | Implement 3-tier model strategy (Cached/Mock). | Active | Resource |
| RSK-02 | **Model Download Failures** | Medium | Medium | Blocking deployment/demo. | Pre-download weights into Docker images or bundle scripts. | Active | Technical |
| RSK-03 | **GeoTIFF Edge Cases** | High | High | Preprocessing fails on weird CRSs. | Strict rasterio validation, normalize to 8-bit RGB early. | Active | Data |
| RSK-04 | **SAR Data Complexity** | High | Medium | Poor model performance on SAR. | Treat as grayscale; rely on cross-modal comparison; do not force VQA on SAR alone. | Active | Data |
| RSK-05 | **Cross-Modal Alignment** | High | High | False change detection due to misalignment. | Add automated co-registration step in preprocessing. | Active | Technical |
| RSK-06 | **Team Skill Level (ML)** | Medium | Low | Fine-tuning might fail. | Fallback to zero-shot models with strong prompting. | Active | Resource |
| RSK-07 | **Memory Overflow (OOM)** | High | High | App crashes during multi-step queries. | Batch processing; unload models dynamically; quantize to 4-bit. | Active | Technical |
| RSK-08 | **API Contract Changes** | Low | Low | Breaks frontend. | Strict Pydantic models; versioning (`/v1/`). | Monitored | Integration |
| RSK-09 | **Model Licensing** | High | Low | Disqualified from hackathon. | Only use Apache 2.0 or open weights. | Closed | Compliance |
| RSK-10 | **Dataset Accessibility** | Medium | Medium | Cannot get fine-tuning data. | Pre-scrape small subset; rely on open huggingface datasets. | Monitored | Data |
| RSK-11 | **Eval Data Quality** | Medium | Low | Benchmarks lie. | Manual review of 100 test samples. | Monitored | Data |
| RSK-12 | **Windows Specific Issues** | Medium | High | Paths/OS errors during data load. | Use `pathlib` strictly; test on WSL/Linux for production. | Active | Technical |
| RSK-13 | **Fine-Tuning Instability** | High | Medium | LoRA corrupts model. | Keep base model; only load LoRA if eval shows improvement. | Active | Model |
| RSK-14 | **VLM Hallucination** | High | High | System invents evidence. | Strict prompt engineering; Evidence objects demand Confidence scores. | Active | Model |
| RSK-15 | **Frontend Integration** | High | Medium | UI cannot parse complex evidence. | Send flat JSON arrays of bounding boxes; keep API simple. | Active | Integration |
