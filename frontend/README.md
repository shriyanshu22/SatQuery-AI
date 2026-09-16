# GeoLens — Frontend

Evidence-first, agentic interface for multimodal remote-sensing image analysis.
Built for Smart India Hackathon 2026, Problem Statement SIH26167.

This is **Part 1 of 4**: foundation, architecture, and core UI. It is a fully
independent frontend client — it does not import backend code, invoke models,
or reproduce any analysis logic. It talks to a backend only through the
`SatQueryApiClient` interface in `src/api/client.ts`.

## What's implemented in this part

- Project scaffold: Vite + React + TypeScript + Tailwind CSS v4
- Application shell: header (branding, backend status, demo mode indicator),
  asymmetric two-column workspace (imagery + query on the left, status +
  help on the right)
- Upload flow: drag-and-drop + file picker, per-image state machine
  (uploading → processing → ready / failed), metadata display, validation
  display (valid / warning / invalid) sourced entirely from the API layer
- Query composer: natural-language input with example prompts, no forced
  model/pipeline selection
- Analysis status: execution trace panel, expandable technical evidence
  section (collapsed by default — the default experience stays simple)
- Full component state coverage: empty, loading, success, warning, error
  for every major surface
- Mock API layer (`src/api/mock/`) so the app is fully demoable with zero
  backend — swap to a real backend by implementing `SatQueryApiClient` in
  `src/api/real/` and flipping `VITE_API_MODE=real`. See `src/api/README.md`.

## Landing page

`src/pages/Landing.tsx` is the entry screen: logo lockup, headline, and a
choice between two ways to proceed — **Researcher** (full upload + analysis
flow) and **Explore** (sample-scene demo mode).

`src/Root.tsx` is the gate that connects it to the main workspace: it holds
which role was picked and renders `Landing` until one is chosen, then renders
`App` with that role. `main.tsx` mounts `Root` instead of `App` directly.
`App` shows the picked mode as a badge in the header (`Header.tsx`), next to
a "Change mode" link that clears the selection and returns to the landing
page.

## Not yet built (Parts 2–4)

Change-detection maps, grounding/bounding-box overlays, SAR/optical
comparison views, the fuller evidence viewer, report generation, and real
backend wiring — the folders for these already exist under
`src/features/` so later parts extend rather than restructure.

## Running it

```bash
npm install
cp .env.example .env
npm run dev
```

Runs entirely on the mock API by default — no backend required to see the
full upload → ask → analyze flow.

## Design system

- Base: deep petrol teal-navy (`#0f2229`), evoking optics glass and ocean
  seen from orbit — panels lift with `#16303a` / `#1c3944` and soft
  shadows, not hairline borders
- Accent: warm terracotta (`#e08a5b`), glowing with confident contrast
  against the deep teal; secondary data color is a warm sand
  (`#e3c581`) — used for real technical values, never for cheerful UI
  chrome
- Type: IBM Plex Sans for UI, IBM Plex Mono reserved for genuinely
  technical values (file sizes, CRS, coordinates, evidence numbers)
- Status is always icon + color + text, never color alone
