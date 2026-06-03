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
- **Current scaffold:** Poll or consume the localhost read surface (GET /health, /run/current, /run/stats, /events, /receipts, /gates, /traces, /warnings). TUI: read/render-only display + CLI. HTML: view-only stats/graphs/readouts/exports.
- Display engine-owned gate results, receipts, warnings, and telemetry
- Render snapshots, timelines, and stats for operator awareness
- **Future target (TUI only):** Translate operator gestures into request objects to be forwarded by a thin relay *to a gated Engine command API only*. (Not implemented in this scaffold/repo phase. Engine decides/ gates / executes.)
- Export static read-only HTML snapshots of observed data (HTML role remains view-only)

## Hard Prohibitions (this repo — permanent)
- No imports of `act_mce.*` (engine, gates, capabilities, registry, runtime, receipts writer, etc.) — ever.
- No POST / PUT / PATCH / DELETE against any surface — ever.
- No direct command execution, shell, pty, or capability invocation — ever (TUI may only request via future gated Engine API).
- No gate evaluation or readiness synthesis — ever.
- No writing receipts or mutating run artifacts directly — ever.
- No phase advancement, no "approve", no "execute", no "advance" actions in UI — ever.
- No claiming "ready", "accepted", "final acceptance", or operator sign-off unless the engine gate result says so — ever.
- TUI must never directly execute capabilities, mutate engine state, bypass gates, write receipts, or self-approve.
- HTML surface: view-only permanently (stats, graphs, readouts, exports); runs in browser sandbox; no direct local access.

## Kernel Statement
"Viewer observes. Engine decides. Gates decide advancement. Operator acceptance remains final."

Any code that violates the above produces a boundary violation. Tests in this repo enforce the contract at import time and at the level of implemented routes/actions.

## Consumers of this Boundary
- act_tui_html_hybrid.read_surface_client (pure GET consumer for live read surface; fixture loads are preview-only and separate)
- act_tui_html_hybrid.tui (**current scaffold:** observation + read/render-only display + CLI read commands. **Future target:** operator request/input surface via gated Engine command API only. Never direct execution/mutation.)
- act_tui_html_hybrid.html_export (view-only static rendering permanently in this repo — stats/graphs/readouts/exports; Phase 2 improved HTML + CLI)

Fixture data is explicitly marked SAMPLE/PREVIEW and must not be used to simulate engine decisions.

See also: docs/READ_SURFACE_CONTRACT.md and README.md.
