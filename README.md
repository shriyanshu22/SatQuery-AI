# SatQuery AI
[![SIH26167](https://img.shields.io/badge/SIH-26167-blue.svg)](https://sih.gov.in)

SatQuery AI is an interactive vision-language assistant designed for multimodal remote sensing image analysis through intuitive text queries. It aims to bridge the gap between complex geospatial data and natural language, enabling intuitive exploration and analysis of satellite imagery.

## Key Capabilities
- **Visual Question Answering (VQA)**: Ask questions about satellite images and get detailed textual answers.
- **Visual Grounding**: Locate specific objects or regions in an image based on textual descriptions, returning bounding boxes.
- **Change Detection**: Analyze two images of the same area over time to identify and describe changes.
- **Cross-modal Analysis**: Fuse text and image features to provide comprehensive insights.
- **Model Adaptation**: Readily adaptable to different underlying Vision-Language Models (VLMs) and task-specific models.

## Architecture Overview
The system follows a layered architecture to ensure separation of concerns and testability:
`api` → `agents` → `services` → `models` → `preprocessing` → `core`

- **core**: Contains foundational data types (Evidence, Confidence).
- **models**: Implements three tiers of execution: RealModel (live inference), MockModel (deterministic testing), and CachedModelOutput (replays).

For a deep dive, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quick Start

1. Create a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
4. Run the server:
   ```bash
   uvicorn backend.api.main:app --reload
   ```

## Project Structure
```
c:\coding\SatQueryAI-SIH26
├── backend/            # FastAPI backend code
├── configs/            # YAML configuration files
├── data/               # Datasets, model weights, demo data
├── docs/               # Project documentation
├── frontend/           # Notes on frontend separation
├── outputs/            # Temporary outputs and logs
├── scripts/            # Utility scripts (download models, run demo)
├── .env.example        # Example environment variables
├── .gitignore          # Git ignore rules
├── AGENTS.md           # Instructions for AI agents
├── README.md           # This file
└── requirements.txt    # Python dependencies
```

## Development
- **Running Tests**: Tests are located in `backend/tests/`. Use `pytest` to run them.
- **Demo Mode**: Run the demo script `python scripts/run_demo.py` to start the application with mock or cached models for demonstration without requiring a GPU.

## Documentation Links
- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [API_CONTRACT.md](docs/API_CONTRACT.md)
- [FRONTEND_CONTRACT.md](docs/FRONTEND_CONTRACT.md)

## License
[Placeholder for License]

## Team
Developed for Smart India Hackathon 2026 (SIH26167) by our team of first-year engineering students.
