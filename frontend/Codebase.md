# SatQuery AI (GeoLens) — Codebase Technical Reference

> **Project**: SatQuery AI / GeoLens (`satquery-ai`)  
> **Initiative**: Smart India Hackathon 2026 — Problem Statement **SIH26167**  
> **Domain**: Evidence-First, Agentic Multimodal Remote-Sensing Imagery Analysis  
> **Current Version**: Complete Master Prompt Implementation

---

## 1. Directory Structure

```
SIH FRONTEND/
├── docs/                               # Standardized contract documentation
│   ├── FRONTEND_ARCHITECTURE.md        # Master frontend system design
│   ├── FRONTEND_COMPONENT_MAP.md       # Component catalog & prop specifications
│   ├── FRONTEND_INTEGRATION.md         # FastAPI integration & endpoint schemas
│   └── FRONTEND_API_MISMATCHES.md      # Discrepancy tracking log
├── Architecture.md                     # High-level architecture, state machines & diagrams
├── Codebase.md                         # This file — technical component & file reference
├── Readme.md                           # Executive overview & quick-start guide
└── geolens-frontend-landing/
    └── satquery-ai/
        ├── .env.example                # Sample environment configuration
        ├── .gitignore                  # Git ignore rules
        ├── .oxlintrc.json              # Oxlint fast linter configuration
        ├── index.html                  # HTML entry point with IBM Plex Google Fonts
        ├── package.json                # React 19, Recharts, Leaflet, Tailwind v4
        ├── package-lock.json           # Dependency lockfile
        ├── tsconfig.json               # Root TypeScript configuration
        ├── tsconfig.app.json           # Application TypeScript settings (path alias @/*)
        ├── tsconfig.node.json          # Node/Vite build tools settings
        ├── vite.config.ts              # Vite 8 config with React & Tailwind v4 plugins
        └── src/
            ├── main.tsx                # React 19 bootstrap mounting <Root />
            ├── Root.tsx                # Mode/role router gate (Landing vs App)
            ├── App.tsx                 # Analytical workspace orchestrator
            ├── index.css               # Tailwind CSS v4 custom @theme palette
            ├── api/
            │   ├── client.ts           # SatQueryApiClient interface boundary
            │   ├── index.ts            # Client factory (mock vs real switcher)
            │   ├── upload.ts           # Upload endpoint wrapper
            │   ├── analysis.ts         # Query submission & polling wrapper
            │   ├── results.ts          # Report & artifact download wrapper
            │   ├── demo.ts             # Demo scenario data fetcher
            │   └── mock/
            │       └── mockClient.ts   # Task simulator (VQA, Grounding, Change, Killer Query)
            ├── components/
            │   ├── EmptyState.tsx      # Null-state fallback card
            │   ├── ErrorPanel.tsx      # Danger/error alert container
            │   ├── GeospatialMapViewer.tsx # Leaflet-styled spatial reference HUD
            │   ├── Header.tsx          # Top navigation bar & connection badge
            │   ├── HelpPanel.tsx       # Informational sidebar guide
            │   ├── ImageCard.tsx       # Uploaded image preview, status & metadata
            │   ├── ImageMetadata.tsx   # Detailed image technical properties list
            │   ├── Layout.tsx          # 2-column asymmetric desktop grid
            │   ├── LoadingState.tsx    # Accessible loading spinner
            │   ├── Panel.tsx           # Standardized glass panel container
            │   ├── Sidebar.tsx         # Sidebar wrapper
            │   ├── StatusBadge.tsx     # Semantic micro-badges (5 status states)
            │   ├── WarningPanel.tsx    # Cautionary notice card
            │   └── icons.tsx           # Handcrafted standalone SVG icons
            ├── features/
            │   ├── analysis/
            │   │   ├── AnalysisStatusPanel.tsx   # Observable execution trace timeline
            │   │   ├── AnalysisSummaryPanel.tsx  # Master results container
            │   │   ├── AnalyzeButton.tsx         # Primary action trigger button
            │   │   ├── AnswerCard.tsx            # Prominent primary finding card
            │   │   ├── ConfidenceCard.tsx        # Calibrated confidence score & explanation
            │   │   ├── EvidenceGallery.tsx       # Polymorphic evidence router
            │   │   ├── QueryComposer.tsx         # Natural-language query input box
            │   │   ├── ReportDownload.tsx        # Backend artifact download button
            │   │   └── TechnicalDetailsPanel.tsx # Expandable model provenance inspector
            │   ├── change-detection/
            │   │   ├── BeforeAfterViewer.tsx     # Split slider, side-by-side & change map
            │   │   └── ChangeMetricsChart.tsx    # Recharts quantitative change metrics
            │   ├── cross-modal/
            │   │   └── OpticalSarViewer.tsx      # Optical vs SAR dual-sensor corroborator
            │   ├── demo/
            │   │   └── DemoSelector.tsx          # Pre-configured dataset loader
            │   ├── grounding/
            │   │   ├── BoundingBoxOverlay.tsx    # Spatial raster coordinate mapping
            │   │   └── GroundingViewer.tsx       # Category-filtered grounding container
            │   └── upload/
            │       └── UploadDropzone.tsx        # Drag & drop file ingest area
            ├── hooks/
            │   ├── useAnalysis.ts      # Query submission & polling state
            │   └── useImageUpload.ts   # Upload queue, object URL memory & demo staging
            ├── pages/
            │   └── Landing.tsx         # Landing page hero & role selector
            ├── types/
            │   ├── analysis.ts         # Query, trace step, technical details & result
            │   ├── api.ts              # API schemas, task types & confidence models
            │   ├── demo.ts             # Demo dataset & sample schemas
            │   ├── evidence.ts         # Generic polymorphic evidence discriminated union
            │   ├── image.ts            # Image metadata, validation & role types
            │   └── metadata.ts         # Extended geospatial properties
            └── utils/
                └── format.ts           # Byte size, modality & role formatters
```

---

## 2. Evidence System & Specialized Viewers

### 2.1 Polymorphic Evidence Router (`EvidenceGallery.tsx`)
Inspects `evidence.type` and renders the corresponding component:
- `bounding_box`: Routed to `<GroundingViewer />` and `<BoundingBoxOverlay />`. Maps normalized coordinates `[ymin, xmin, ymax, xmax]` directly onto image pixels.
- `change_map`: Routed to `<BeforeAfterViewer />`. Supports split slider, side-by-side view, and change heatmap masks.
- `cross_modal`: Routed to `<OpticalSarViewer />`. Renders Optical vs SAR observations with agreement status (`agree`, `disagree`, `inconclusive`).
- `numerical`: Routed to `<ChangeMetricsChart />`. Renders quantitative time-series charts using **Recharts**.
- `text`: Renders verified ground truth fact cards with provenance citations.
- `image` / `crop`: Renders focused visual evidence crops.

### 2.2 Confidence Model (`ConfidenceCard.tsx`)
- Strictly distinguishes between `available` and `unavailable` states.
- Displays calibrated or model-derived scores with method badges (`Calibrated Confidence`, `Model-Derived`, `Evidence-Derived`).
- Never fabricates scores or substitutes agreement percentages for confidence.

### 2.3 The "Killer Query" Cross-Modal Workflow
Implements Master Prompt Section 33:
> *"Did urban development increase between these dates, and can SAR support the result?"*
1. Ingests bi-temporal optical scenes + Sentinel-1 SAR scene.
2. Follows a 6-step observable execution trace.
3. Renders the prominent `<AnswerCard />`: confirming +38.4 hectares increase.
4. Renders `<ConfidenceCard />`: 94% calibrated cross-sensor confidence.
5. Renders `<OpticalSarViewer />`: showing positive corroboration (`agree`), optical NDBI evidence, and SAR double-bounce microwave backscatter permanence.
6. Renders `<BeforeAfterViewer />` and `<ChangeMetricsChart />`: interactive split comparison and multi-year urban growth trend.
7. Offers `<ReportDownload />`: downloadable analysis report artifact.
