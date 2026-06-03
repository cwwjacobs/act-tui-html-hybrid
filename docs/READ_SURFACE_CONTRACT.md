# ACT TUI/HTML Hybrid — Read Surface Contract

## Purpose
Defines the narrow, read-only HTTP surface (the "read surface") that the ACT TUI/HTML Hybrid viewer is permitted to consume from an ACT-MCE localhost read server.

**This read surface contract is always observation-only (GET consumption only).** The read server is a thin relay serving engine-owned artifacts. The viewer never owns truth via the read surface.

**Overall viewer roles (distinguished):**
- Current scaffold phase (this repo): TUI is read/render-only (no request submission yet). HTML is view-only (stats/graphs/readouts/exports).
- Future target (TUI): may become operator request/input surface, submitting requests *only* through a future gated Engine command API. Engine owns execution, gates, decisions, receipts. TUI never directly executes/mutates/bypasses/writes/self-approves.
- HTML remains view-only.

## Base URL
Default: `http://127.0.0.1:8765`

Configurable via `ReadSurfaceClient(base_url=...)`.

## Allowed Methods
**GET only.** Every implemented method on the client performs exactly one GET.

No other verbs are coded or exposed.

## Endpoints
- `GET /health`
  - Returns: `{ "schema_version": "act_viewer_server.health.v0_1", "status": "OK", "service": "...", "read_only": true }`
- `GET /run/current`
  - Returns current Stage 1 admission snapshot (or UNKNOWN fallback when no engine gate result present).
- `GET /run/stats`
  - Aggregate counts (events, receipts, gates, traces, warnings).
- `GET /events`
  - Event records (read-only telemetry; currently empty in Stage 1 minimal).
- `GET /receipts`
  - Receipt summaries. Only engine-owned receipts are surfaced. Missing → empty list + warnings.
- `GET /gates`
  - Gate summaries. Engine gate result is rendered verbatim (PASS/BLOCKED/UNKNOWN). Viewer does not compute.
- `GET /traces`
  - Trace summaries (empty in minimal Stage 1).
- `GET /warnings`
  - Operator awareness items derived from the engine gate result.

All responses carry `schema_version`, `run_id`, `admission_stage`, `stage_id`, `phase_id`, `source`.

## Graceful Degradation
When the read server is unreachable, each method returns a dict containing:
```json
{
  "error": "Read surface unavailable: ...",
  "source": "read_surface_client",
  "path": "/...",
  "available": false
}
```
Callers (TUI, HTML export) must render the error state without crashing or synthesizing optimistic data.

## Data Semantics
- `status` / `ready` values come from the engine gate result or the explicit `blocked_missing_stage_1_gate_result` fallback.
- `stage_2_allowed` and `stage_1_ready` are echoed from the engine artifact; the viewer never sets them to true on its own.
- No synthetic "PASS", "COMPLETED", or "Continue to Phase 2" may be injected when the engine result is absent.

## Versioning
Endpoints and payloads are versioned via `schema_version` strings (e.g. `act_viewer.localhost.run_current.v0_1`).

## Enforcement
- Static analysis in tests: source must contain no POST/PUT/PATCH/DELETE, no "act_mce.gates", no "capability", no "runner", no "execution".
- Runtime: client uses only `urllib.request.Request(..., method="GET")` for live paths. Fixture loading is isolated preview path. (No write paths exist.)
- **Current scaffold:** TUI and HTML layers only call read methods (or fixture load), render improved layouts, and expose only read subcommands in CLI. No command submission / input surfaces implemented.
- README and docs/BOUNDARY.md now distinguish: current read-only scaffold (TUI read/render, HTML view-only) vs. future gated TUI request/input surface (through Engine API). Permanent forbids documented.
- Phase 2 adds visual refinements and CLI (read-only today) but does not relax any prohibitions and does not implement request submission. Fixtures are for offline preview only and carry explicit SAMPLE markers.

## Related
- docs/BOUNDARY.md
- The read server implementation (in ACT-MCE) under `act_viewer_server/`
- Cards: card_localhost_backend_routes_only, card_event_stream_read_only, card_viewer_observe_request_only, card_html_telemetry_only, card_textual_operator_surface, card_browser_safety_boundary

This *read surface* contract is observation-only (GET consumption). The overall TUI (current scaffold: read/render-only; future: gated requests only) and HTML (view-only) obey the architecture: Engine decides, gates, executes, emits receipts. TUI never owns truth, execution, or acceptance. Operator review of engine gate results remains authoritative.
