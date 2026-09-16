# GeoLens Frontend — System Architecture

> **Project**: GeoLens (`satquery-ai`)  
> **Initiative**: Smart India Hackathon 2026 — Problem Statement **SIH26167**  
> **Architecture Pattern**: Hexagonal (Ports & Adapters) + Component-Driven Unidirectional Flow  
> **Target Environment**: Web Client (React 19, TypeScript, Vite, Tailwind CSS v4)

---

## 1. Architectural Philosophy

GeoLens is an **evidence-first, agentic interface** designed for multimodal remote-sensing image analysis. Unlike conventional black-box conversational systems, GeoLens prioritizes technical auditability, trace visibility, and grounded verification.

### Core Tenets
1. **Evidence-First Verification**: Every analytical claim presented to the user is backed by an inspectable execution trace and discrete evidence metrics (bounding regions, pixel classifications, spectral indices).
2. **Ports & Adapters (Hexagonal) API Separation**: The UI and feature logic are completely decoupled from the transport and backend implementations. All network operations communicate exclusively through the `SatQueryApiClient` interface.
3. **Modal-Agnostic Ingestion**: Supports single scenes, temporal pairs (before/after), and cross-sensor pairs (Optical + Synthetic Aperture Radar - SAR) through heuristic role inference.
4. **Resilient Offline / Demo Capability**: The architecture features a self-contained in-memory mock engine that runs fully offline without requiring an active AI backend.

---

## 2. High-Level System Topology

```mermaid
flowchart TD
    subgraph Client ["Browser Client (React 19 + TypeScript)"]
        Landing["Landing Page (Role Selection)"]
        RootGate["Root Router Gate"]
        AppShell["App Workspace Shell"]

        subgraph Features ["Feature Modules"]
            UploadModule["Upload Dropzone & Processing"]
            QueryModule["Natural Language Query Composer"]
            TraceModule["Execution Trace Status Panel"]
            SummaryModule["Analysis Summary & Evidence Drawer"]
        end

        subgraph Hooks ["Custom State Hooks"]
            UseUpload["useImageUpload (State & Role Heuristics)"]
            UseAnalysis["useAnalysis (Query & Polling State)"]
        end

        subgraph PortLayer ["API Port Layer"]
            ClientInterface["SatQueryApiClient Interface"]
        end

        subgraph Adapters ["API Adapters"]
            MockAdapter["Mock Client (In-Browser Simulation)"]
            RealAdapter["Real Client (REST / HTTP Backend) [Future]"]
        end
    end

    subgraph Backend ["Remote Sensing Backend / AI Pipeline"]
        FastAPI["FastAPI / Flask Server"]
        VisionModels["Object Detection & Segmentation"]
        ChangeEngine["Bi-Temporal Change Engine"]
        SARFusion["Cross-Modal SAR + Optical Fusion"]
    end

    RootGate -->|Selects Role| Landing
    RootGate -->|Enters Workspace| AppShell
    AppShell --> Features
    Features --> Hooks
    Hooks --> ClientInterface
    ClientInterface -->|VITE_API_MODE=mock| MockAdapter
    ClientInterface -.->|VITE_API_MODE=real| RealAdapter
    RealAdapter -.->|HTTP / REST| FastAPI
    FastAPI --> VisionModels & ChangeEngine & SARFusion
```

---

## 3. Layered Application Architecture

GeoLens adopts a four-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│    Landing Page · Header · ImageCard · QueryComposer        │
│   AnalysisStatusPanel · AnalysisSummaryPanel · Badges       │
├─────────────────────────────────────────────────────────────┤
│                    Application State Layer                  │
│       useImageUpload (Queue, Blob URLs, Role Inference)     │
│       useAnalysis (Execution Trace, Result, Polling)        │
├─────────────────────────────────────────────────────────────┤
│                      Domain & Types                         │
│           ImageMetadata · Validation · ExecutionTrace       │
│           EvidenceItem · AnalysisQuery · Modality           │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure (API) Layer                 │
│        SatQueryApiClient Interface · MockClient · Env       │
└─────────────────────────────────────────────────────────────┘
```

### 1. Presentation Layer (`src/components/`, `src/features/`, `src/pages/`)
- **Presentational / Dumb Components**: Reusable, pure UI components (`Panel`, `StatusBadge`, `EmptyState`, `ErrorPanel`, `WarningPanel`, `icons`). They receive data and event handlers via standard props.
- **Feature Composites**: Stateful composites (`UploadDropzone`, `QueryComposer`, `AnalysisSummaryPanel`) that coordinate UI interaction patterns.

### 2. Application State Layer (`src/hooks/`)
- Encapsulates stateful workflows, async lifecycle transitions, and memory management.
- Pure React hooks (`useImageUpload`, `useAnalysis`) with zero coupling to DOM or backend mechanics.

### 3. Domain & Types Layer (`src/types/`, `src/utils/`)
- Strongly typed TypeScript contracts modeling remote-sensing data structures.
- Formatters and converters ensuring consistent tabular representations.

### 4. Infrastructure Layer (`src/api/`)
- Pure client interface abstractions allowing zero-touch switching between mock simulation and production backend environments.

---

## 4. State Machines & Lifecycles

### 4.1 Root Navigation & Role State Machine
Manages user onboarding and mode switching.

```mermaid
stateDiagram-v2
    [*] --> RoleSelection: App Launch
    RoleSelection --> LandingView: role === null
    LandingView --> ResearcherWorkspace: Select Researcher Mode
    LandingView --> ExploreWorkspace: Select Explore Mode
    ResearcherWorkspace --> RoleSelection: Click "Change mode"
    ExploreWorkspace --> RoleSelection: Click "Change mode"
```

### 4.2 Image Upload & Validation State Machine
Each image added to the workspace operates as an independent state machine.

```mermaid
stateDiagram-v2
    [*] --> Queued: User drops file
    Queued --> Uploading: Blob preview created & upload initiated
    Uploading --> Processing: Progress hits 100%
    Uploading --> Failed: Network/Format error
    Processing --> ReadyValid: Validation passes (status: valid)
    Processing --> ReadyWarning: Validation flags warnings (status: warning)
    Processing --> Failed: Critical validation issue (status: invalid)
    ReadyValid --> [*]: User clicks delete (Blob revoked)
    ReadyWarning --> [*]: User clicks delete (Blob revoked)
    Failed --> [*]: User clicks remove
```

### 4.3 Query Analysis Lifecycle
Manages user query execution and trace updates.

```mermaid
stateDiagram-v2
    [*] --> Idle: Images Ready
    Idle --> Submitting: User triggers "Analyze"
    Submitting --> Running: Backend returns analysis ID & initial trace
    Running --> Succeeded: Final result received (trace done)
    Running --> Warning: Result received with anomaly warnings
    Running --> Failed: Network or pipeline exception
    Succeeded --> Idle: Reset or new query
    Warning --> Idle: Reset or new query
    Failed --> Idle: User re-tries query
```

---

## 5. Domain Logic & Algorithms

### 5.1 Heuristic Modality & Multi-Sensor Pair Detection
Remote sensing imagery can represent various sensors and acquisition windows. GeoLens automatically identifies the semantic relationship among uploaded scenes without requiring manual user tagging.

```mermaid
flowchart TD
    Start[Uploaded Scenes in 'Ready' Stage] --> CountCheck{Count < 2?}
    CountCheck -- Yes --> Single[Role: 'single']
    CountCheck -- No --> CheckSensors{Has SAR + (Optical or MS)?}
    CheckSensors -- Yes --> AssignCrossModal[Assign 'sar-pair' to SAR, 'optical-pair' to Optical/MS]
    CheckSensors -- No --> AssignTemporal[Assign Temporal Roles by Upload Chronology: First = 'temporal-before', Subsequent = 'temporal-after']
```

#### Modality Detection Rules:
- Filename contains `sar` $\to$ `ImageModality: 'sar'` (Bands: 1)
- Filename contains `ms` or `multispectral` $\to$ `ImageModality: 'multispectral'` (Bands: 8)
- File extension `.tif` or `.tiff` $\to$ `ImageModality: 'optical'` (Bands: 3)
- Default $\to$ `ImageModality: 'unknown'`

### 5.2 Memory-Safe Object URL Lifecycle Management
To render high-resolution raster imagery instantly in the browser without waiting for cloud round-trips:
1. `URL.createObjectURL(file)` is invoked upon drop.
2. The generated URL is registered into a persistent `useRef<Set<string>>` pool.
3. When the user removes an image, `removeImage(id)` queries the pool and executes `URL.revokeObjectURL(url)`.
4. This prevents memory leaks from accumulating large satellite raster files in browser heap memory.

---

## 6. End-to-End Sequence Workflows

### 6.1 Upload & Metadata Ingestion Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Dropzone as UploadDropzone
    participant Hook as useImageUpload
    participant API as SatQueryApiClient
    participant Server as Backend Server

    User->>Dropzone: Drops satellite image file
    Dropzone->>Hook: addFiles([file])
    Hook->>Hook: Create local object URL & placeholder
    Hook->>API: uploadImage(file, onProgress)
    API->>Server: POST /api/v1/upload (multipart/form-data)
    Server-->>API: Progress updates (10%, 35%, ... 100%)
    API-->>Hook: onProgress(pct)
    Server-->>API: 200 OK (metadata, validation, remotePreviewUrl)
    API-->>Hook: Resolve metadata & validation
    Hook->>Hook: Run inferRoles() & set stage='ready'
    Hook-->>User: Render ImageCard with metadata & badges
```

### 6.2 Query Submission & Execution Trace Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Composer as QueryComposer
    participant Hook as useAnalysis
    participant API as SatQueryApiClient
    participant Trace as AnalysisStatusPanel
    participant Summary as AnalysisSummaryPanel

    User->>Composer: Enters query & hits "Analyze"
    Composer->>Hook: runQuery(prompt, [readyImageIds])
    Hook->>API: submitQuery({ prompt, imageIds })
    API-->>Hook: Returns running AnalysisResult (initial trace)
    Hook->>Trace: Render active trace step
    Hook->>API: getAnalysis(analysisId)
    API-->>Hook: Returns succeeded AnalysisResult (completed trace + summary + evidence)
    Hook->>Trace: Update trace steps to 'done'
    Hook->>Summary: Render summary, warnings & technical evidence drawer
```

---

## 7. Connecting a Real Backend (Integration Guide)

Connecting GeoLens to a production backend (e.g. FastAPI, Python Flask, or Node.js) requires implementing the `SatQueryApiClient` interface in a new adapter file:

### Step 1: Create `src/api/real/realClient.ts`

```typescript
import type { SatQueryApiClient } from '../client'
import type { ImageMetadata, ImageValidation } from '@/types/image'
import type { AnalysisResult } from '@/types/analysis'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const realClient: SatQueryApiClient = {
  async uploadImage(file, onProgress) {
    const formData = new FormData()
    formData.append('file', file)

    const xhr = new XMLHttpRequest()
    return new Promise((resolve, reject) => {
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100))
        }
      }
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText))
        } else {
          reject(new Error(xhr.statusText))
        }
      }
      xhr.onerror = () => reject(new Error('Network error during image upload'))
      xhr.open('POST', `${BASE_URL}/api/v1/images/upload`)
      xhr.send(formData)
    })
  },

  async submitQuery(query) {
    const res = await fetch(`${BASE_URL}/api/v1/analysis/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(query),
    })
    if (!res.ok) throw new Error('Query submission failed')
    return res.json()
  },

  async getAnalysis(analysisId) {
    const res = await fetch(`${BASE_URL}/api/v1/analysis/${analysisId}`)
    if (!res.ok) throw new Error('Failed to fetch analysis status')
    return res.json()
  },

  async checkBackendStatus() {
    try {
      const res = await fetch(`${BASE_URL}/health`, { method: 'GET' })
      return { online: res.ok, mode: 'real' }
    } catch {
      return { online: false, mode: 'real' }
    }
  }
}
```

### Step 2: Update `src/api/index.ts`
Switch `createClient()` to return `realClient` when `mode === 'real'`.

### Step 3: Configure `.env`
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_MODE=real
```

---

## 8. Extensibility Roadmap (Parts 2 to 4)

The project directory structure already reserves designated folders for subsequent implementation phases:

| Phase | Feature Focus | Target Module | Technical Scope |
|---|---|---|---|
| **Part 1** | Foundation & Core UI | `upload/`, `analysis/`, `pages/` | Workspace shell, upload dropzone, role heuristics, mock pipeline, landing page |
| **Part 2** | Geospatial Grounding & Map View | `features/grounding/` | Leaflet (`react-leaflet`) map integration, GeoJSON layer overlay, bounding-box visualizers |
| **Part 3** | Change Detection & Cross-Modal Fusion | `features/change-detection/`, `features/cross-modal/` | Dual-view split comparison slider, difference heatmaps, optical vs SAR registration views |
| **Part 4** | Advanced Reporting & Production Real Client | `src/api/real/`, `features/demo/` | Automated PDF/GeoTIFF report exporter, real model API connection, telemetry and benchmarking |
