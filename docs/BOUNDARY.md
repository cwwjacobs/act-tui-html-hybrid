# ACT TUI/HTML Hybrid — Engine / Viewer Boundary

**Prime Law**:
The Engine owns workflow logic, state transitions, receipts, gates, and execution.
The Viewer (TUI + HTML) observes and may submit requests only.

## What ACT-MCE (Engine) Owns
- Capability execution (shell, pty, local_model, wrappers, etc.)
- Run State transitions and phase/stage advancement
- Receipt generation and signing
- Gate evaluation (SchemaGate, PermissionGate, Stage1AdmissionGate, ...)
- Trace recording and export
- Deciding readiness, admission, and advancement

## What the TUI/HTML Hybrid Viewer May Do
- Poll or consume the localhost read surface (GET /health, /run/current, /run/stats, /events, /receipts, /gates, /traces, /warnings)
- Display engine-owned gate results, receipts, warnings, and telemetry
- Render snapshots, timelines, and stats for operator awareness
- Translate operator gestures into request objects (future) to be forwarded by a thin relay
- Export static read-only HTML snapshots of observed data

## Hard Prohibitions (this repo)
- No imports of `act_mce.*` (engine, gates, capabilities, registry, runtime, receipts writer, etc.)
- No POST / PUT / PATCH / DELETE against any surface
- No command execution, shell, pty, or capability invocation
- No gate evaluation or readiness synthesis
- No writing receipts or mutating run artifacts
- No phase advancement, no "approve", no "execute", no "advance" actions in UI
- No claiming "ready", "accepted", or "operator acceptance" unless the engine gate result says so
- HTML surface runs in browser sandbox; no direct local access

## Kernel Statement
"Viewer observes. Engine decides. Gates decide advancement. Operator acceptance remains final."

Any code that violates the above produces a boundary violation. Tests in this repo enforce the contract at import time and at the level of implemented routes/actions.

## Consumers of this Boundary
- act_tui_html_hybrid.read_surface_client (pure GET consumer)
- act_tui_html_hybrid.tui (observation + display only)
- act_tui_html_hybrid.html_export (read-only static rendering)

See also: docs/READ_SURFACE_CONTRACT.md and README.md.
