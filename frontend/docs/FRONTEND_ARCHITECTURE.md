# SatQuery AI — Frontend Architecture Document

> **Initiative**: Smart India Hackathon 2026  
> **Problem Statement**: SIH26167  
> **Project**: SatQuery AI (GeoLens)  
> **Core Architectural Rule**: Frontend is an independent client of SatQuery's API, not part of the AI system itself.

---

## 1. System Topology & Design Philosophy

SatQuery AI is an **evidence-first, agentic interface for multimodal remote-sensing image analysis**.

### 1.1 Key Principles
1. **Strict Client Boundary**: The frontend never imports Python modules, model code, or executes computer vision logic in JavaScript. It relies strictly on the backend REST API.
2. **Ports & Adapters (Hexagonal) Pattern**: All feature components and state hooks interact with an abstract client interface (`SatQueryApiClient`). Swapping between the mock engine and the live FastAPI backend is governed by `VITE_API_MODE`.
3. **Evidence-Driven UI**: The UI dynamically renders specialized viewers based on `evidence.type` (bounding boxes, change maps, optical+SAR cross-modal comparisons, Recharts time-series metrics).
4. **Observable Execution Tracing**: Only real observable execution events returned by the backend are visualized in the execution timeline. Chain-of-thought and fabricated "AI thinking" animations are strictly prohibited.
5. **Calibrated Confidence**: Confidence is explicitly modeled as a first-class object (`available`, `unavailable`, `calibrated`, `model-derived`, `evidence-derived`). The frontend never fabricates confidence scores.

---

## 2. Directory Layout & Module Structure

```
satquery-ai/
├── src/
│   ├── api/                           # API port & adapter layer
│   │   ├── client.ts                  # SatQueryApiClient interface contract
│   │   ├── index.ts                   # Client factory & switcher
│   │   ├── upload.ts                  # Ingestion endpoints
│   │   ├── analysis.ts                # Query submission & polling
│   │   ├── results.ts                 # Artifact & report downloads
│   │   ├── demo.ts                    # Demo dataset endpoints
│   │   └── mock/
│   │       └── mockClient.ts          # Comprehensive task simulator
│   ├── components/                    # Reusable presentational components
│   │   ├── Header.tsx                 # Navigation & backend status
│   │   ├── Layout.tsx                 # Asymmetric 2-column grid
│   │   ├── Panel.tsx                  # Standardized container card
│   │   ├── ImageCard.tsx              # Raster thumbnail & metadata card
│   │   ├── ImageMetadata.tsx          # Tabular attribute definition list
│   │   ├── StatusBadge.tsx            # Semantic indicator (5 states)
│   │   ├── GeospatialMapViewer.tsx    # Leaflet CRS & spatial HUD
│   │   ├── EmptyState.tsx             # Null-state fallback
│   │   ├── ErrorPanel.tsx             # Error alert
│   │   ├── WarningPanel.tsx           # Warning alert
│   │   └── icons.tsx                  # Handcrafted SVG stroke icons
│   ├── features/                      # Domain-specific feature modules
│   │   ├── upload/
│   │   │   └── UploadDropzone.tsx     # File drag-and-drop ingestion
│   │   ├── analysis/
│   │   │   ├── QueryComposer.tsx      # Natural language prompt composer
│   │   │   ├── AnalyzeButton.tsx      # Action button with loading state
│   │   │   ├── AnswerCard.tsx         # Dominant analytical finding
│   │   │   ├── ConfidenceCard.tsx     # Calibrated confidence display
│   │   │   ├── EvidenceGallery.tsx    # Polymorphic evidence router
│   │   │   ├── AnalysisStatusPanel.tsx# Observable execution timeline
│   │   │   ├── AnalysisSummaryPanel.tsx# Consolidated result container
│   │   │   ├── ReportDownload.tsx     # Backend artifact download
│   │   │   └── TechnicalDetailsPanel.tsx# Expandable provenance inspector
│   │   ├── grounding/
│   │   │   ├── BoundingBoxOverlay.tsx # Spatial raster coordinate mapping
│   │   │   └── GroundingViewer.tsx    # Bounding box & category filter
│   │   ├── change-detection/
│   │   │   ├── BeforeAfterViewer.tsx  # Split-wiper slider & change map
│   │   │   └── ChangeMetricsChart.tsx # Recharts quantitative metrics
│   │   ├── cross-modal/
│   │   │   └── OpticalSarViewer.tsx   # Dual-sensor corroboration viewer
│   │   └── demo/
│   │       └── DemoSelector.tsx       # Pre-configured dataset loader
│   ├── hooks/
│   │   ├── useImageUpload.ts          # Upload queue & role heuristics
│   │   └── useAnalysis.ts             # Analysis lifecycle state
│   ├── types/
│   │   ├── api.ts                     # API contracts & task types
│   │   ├── evidence.ts                # Polymorphic evidence union
│   │   ├── analysis.ts                # Result, trace & confidence types
│   │   ├── image.ts                   # Modality & validation schema
│   │   ├── metadata.ts                # Extended geospatial properties
│   │   └── demo.ts                    # Demo scenario schemas
│   ├── pages/
│   │   └── Landing.tsx                # Hero onboarding & role selection
│   ├── utils/
│   │   └── format.ts                  # Formatter utilities
│   ├── App.tsx                        # Workspace orchestrator
│   ├── Root.tsx                       # Role router / gate
│   └── main.tsx                       # Bootstrap root
```

---

## 3. Data Flow & State Lifecycles

### 3.1 Unidirectional State Architecture
```
[User Action] ──> [Component Event] ──> [Custom Hook] ──> [SatQueryApiClient]
                                                               │
                                                               ▼
[Visual Viewers] <── [React State Update] <── [Validated Typed Response]
```

### 3.2 Polymorphic Evidence Dispatching
The backend supplies an array of `Evidence` objects in `AnalysisResult.evidence`. `EvidenceGallery.tsx` inspects each item's `type` attribute:
- `bounding_box` $\to$ Dispatches to `<GroundingViewer />` mapping `[ymin, xmin, ymax, xmax]` normalized coordinates directly onto image pixels.
- `change_map` $\to$ Dispatches to `<BeforeAfterViewer />` supporting Split Slider, Side-by-Side, and Change Mask overlays.
- `cross_modal` $\to$ Dispatches to `<OpticalSarViewer />` rendering optical vs SAR observations and sensor agreement status (`agree`, `disagree`, `inconclusive`).
- `numerical` $\to$ Dispatches to `<ChangeMetricsChart />` rendering quantitative Recharts series.
- `image` / `crop` $\to$ Renders high-resolution visual evidence crops.
- `text` $\to$ Renders grounded citations with source provenance.
