# API layer

`client.ts` defines `SatQueryApiClient` — the only interface the rest of the
app depends on. `mock/mockClient.ts` implements it with local, in-browser
logic so the UI is fully usable with no backend. `index.ts` picks an
implementation based on `VITE_API_MODE`.

When `/docs/API_CONTRACT.md` (or equivalent) is available, add a
`real/realClient.ts` that implements `SatQueryApiClient` against
`VITE_API_BASE_URL` and wire it into `index.ts`'s `real` branch. No UI code
should need to change — that's the point of the interface boundary.
