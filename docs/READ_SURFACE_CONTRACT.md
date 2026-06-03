# ACT TUI/HTML Hybrid — Read Surface Contract

## Purpose
Defines the narrow, read-only HTTP surface that the ACT TUI/HTML Hybrid viewer is permitted to consume from an ACT-MCE localhost read server.

The contract exists to keep the viewer as a pure observer. The read server is a thin relay serving engine-owned artifacts. The viewer never owns truth.

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
- Runtime: client uses only `urllib.request.Request(..., method="GET")`.
- TUI and HTML layers only call the 8 read methods and render.
- README and docs/BOUNDARY.md restate the observation-only rule.

## Related
- docs/BOUNDARY.md
- The read server implementation (in ACT-MCE) under `act_viewer_server/`
- Cards: card_localhost_backend_routes_only, card_event_stream_read_only, card_viewer_observe_request_only, card_html_telemetry_only, card_textual_operator_surface, card_browser_safety_boundary

This contract is observation surface only. Operator review of engine gate results remains authoritative.
