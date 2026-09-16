# SatQuery AI — Frontend Component Map

> **Initiative**: Smart India Hackathon 2026 | Problem Statement **SIH26167**  
> **Source Directory**: `geolens-frontend-landing/satquery-ai/src/`

---

## 1. Top-Level Views & Layout Shell

| Component | File Path | Props | Purpose |
|---|---|---|---|
| `Root` | `src/Root.tsx` | None | Top-level role router gate switching between `<Landing />` and `<App />`. |
| `Landing` | `src/pages/Landing.tsx` | `onSelectRole(role)` | Visual onboarding page featuring animated orbital SVG and role selection cards. |
| `App` | `src/App.tsx` | `startRole?`, `onChangeMode?` | Core analytical workspace orchestrator coordinating upload, query, results, and status. |
| `Layout` | `src/components/Layout.tsx` | `header`, `main`, `sidebar` | Asymmetric 2-column responsive layout (`1fr_380px` on desktop). |
| `Header` | `src/components/Header.tsx` | `backendOnline`, `startRole?`, `onChangeMode?` | Navigation bar showing branding, active mode badge, and backend connection status. |
| `Sidebar` | `src/components/Sidebar.tsx` | `children` | Sidebar container holding status timeline and spatial reference HUD. |

---

## 2. Ingestion & Preprocessing Components

| Component | File Path | Props | Purpose |
|---|---|---|---|
| `UploadDropzone` | `src/features/upload/UploadDropzone.tsx` | `onFiles(files)` | Drag-and-drop & file picker area accepting `.tif`, `.tiff`, `.geotiff`, and standard imagery. |
| `ImageCard` | `src/components/ImageCard.tsx` | `image`, `onRemove(id)` | Card showing thumbnail, upload progress bar, role tags, and validation issues. |
| `ImageMetadata` | `src/components/ImageMetadata.tsx` | `metadata` | Tabular definition list of technical geospatial attributes (CRS, bands, resolution, date). |

---

## 3. Query & Analytical Results Components

| Component | File Path | Props | Purpose |
|---|---|---|---|
| `QueryComposer` | `src/features/analysis/QueryComposer.tsx` | `disabled`, `isAnalyzing`, `onSubmit(prompt)`, `initialPrompt?` | Natural-language query input box with example query chips and `Cmd+Enter` trigger. |
| `AnalyzeButton` | `src/features/analysis/AnalyzeButton.tsx` | `disabled`, `isAnalyzing`, `onClick()` | Primary action button with spinner animation. |
| `AnswerCard` | `src/features/analysis/AnswerCard.tsx` | `answer`, `task?` | Dominant primary finding card with accent styling and high contrast. |
| `ConfidenceCard` | `src/features/analysis/ConfidenceCard.tsx` | `confidence?` | Structured confidence assessment rendering score, method, and explanation (or "unavailable"). |
| `AnalysisStatusPanel` | `src/features/analysis/AnalysisStatusPanel.tsx` | `result`, `isAnalyzing`, `error` | Observable execution trace timeline showing verified steps. |
| `AnalysisSummaryPanel` | `src/features/analysis/AnalysisSummaryPanel.tsx` | `result`, `defaultImageUrl?`, `onReset?` | Master result panel wrapping AnswerCard, ConfidenceCard, EvidenceGallery, ReportDownload, and TechnicalDetailsPanel. |
| `ReportDownload` | `src/features/analysis/ReportDownload.tsx` | `analysisId`, `filename?`, `format?` | Button triggering backend report generation and download. |
| `TechnicalDetailsPanel` | `src/features/analysis/TechnicalDetailsPanel.tsx` | `details?`, `executionTrace?` | Collapsible accordion revealing model version, processing latency, and execution log. |

---

## 4. Specialized Evidence Viewers

| Component | File Path | Props | Purpose |
|---|---|---|---|
| `EvidenceGallery` | `src/features/analysis/EvidenceGallery.tsx` | `evidence`, `defaultImageUrl?` | Generic polymorphic evidence router dispatching by `evidence.type`. |
| `BoundingBoxOverlay` | `src/features/grounding/BoundingBoxOverlay.tsx` | `imageUrl`, `boxes`, `selectedBoxId?`, `onSelectBox?` | Interactive SVG overlay rendering normalized bounding boxes and labels over image pixels. |
| `GroundingViewer` | `src/features/grounding/GroundingViewer.tsx` | `imageUrl`, `boxes` | Container with detection category filters and localized object inspector. |
| `BeforeAfterViewer` | `src/features/change-detection/BeforeAfterViewer.tsx` | `evidence` | Bi-temporal comparison viewer with Split Slider, Side-by-Side, and Change Map modes. |
| `ChangeMetricsChart` | `src/features/change-detection/ChangeMetricsChart.tsx` | `evidence` | Recharts quantitative metrics chart for surface alteration and temporal trends. |
| `OpticalSarViewer` | `src/features/cross-modal/OpticalSarViewer.tsx` | `evidence` | Dual-sensor comparison viewer with sensor evidence cards and Agreement/Disagreement status. |
| `GeospatialMapViewer` | `src/components/GeospatialMapViewer.tsx` | `centerLat?`, `centerLng?`, `crs?` | Leaflet-based coordinate reference and spatial HUD overlay. |
| `DemoSelector` | `src/features/demo/DemoSelector.tsx` | `onSelectSample(sample)`, `activeSampleId?` | One-click selector staging pre-configured remote-sensing demo packages. |

---

## 5. UI Primitives & Atomic Components

| Component | File Path | Props | Purpose |
|---|---|---|---|
| `Panel` / `PanelHeader` | `src/components/Panel.tsx` | `children`, `title`, `subtitle?`, `action?` | Standardized dark petrol container card with border and header. |
| `StatusBadge` | `src/components/StatusBadge.tsx` | `kind`, `label` | Semantic badge with 5 visual states (`success`, `warning`, `error`, `pending`, `neutral`). |
| `EmptyState` | `src/components/EmptyState.tsx` | `icon?`, `title`, `description?` | Fallback component for blank slates. |
| `ErrorPanel` | `src/components/ErrorPanel.tsx` | `title?`, `description?`, `action?` | Danger/error alert box. |
| `WarningPanel` | `src/components/WarningPanel.tsx` | `title?`, `description?`, `action?` | Cautionary notice box. |
| `LoadingState` | `src/components/LoadingState.tsx` | `label?` | Accessible loading indicator. |
| `icons` | `src/components/icons.tsx` | `SVGProps` | Pure SVG icons (Satellite, Scan, Layers, Compass, Send, Spinner, Trash, etc.). |
