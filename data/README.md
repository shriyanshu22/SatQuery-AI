# Data Directory

This directory stores data utilized by the SatQuery AI system, including demonstration images, evaluation benchmarks, and downloaded model weights.

## Subdirectories

- **`demo/`**: Contains small, real satellite images used for demonstration purposes. These are used when the application runs in demo mode.
- **`benchmarks/`**: Stores evaluation datasets used to assess model performance. Examples include RSVQA-LR, VRSBench, and LEVIR-CD. Note that some of these datasets can be quite large.
- **`models/`**: This directory is used to store downloaded model weights (e.g., `.pt`, `.safetensors`, `.bin`). **This directory is ignored by Git** to prevent uploading massive files to the repository.
- **`downloads/`**: A temporary or cache directory for raw downloaded files before they are processed or moved. **This directory is ignored by Git**.

## Downloading Datasets
For information on how to download specific benchmark datasets, please refer to the respective documentation in `docs/` or evaluation scripts. Do not commit large datasets to this repository.
