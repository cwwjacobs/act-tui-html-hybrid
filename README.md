# act-tui-html-hybrid

**ACT TUI/HTML Hybrid viewer scaffold** — a separate viewer lane for ACT-MCE.

This repository consumes **only** the ACT-MCE localhost read surface. It must never import ACT-MCE engine, gate, capability, registry, execution, or mutation modules.

## Core Rule

> The viewer observes. The engine decides. Gates decide advancement. Operator acceptance remains final.

**Current scaffold phase (this repo):** 
- TUI: read/render-only observation + **local compose/preview of Engine Command Envelopes for ACT-MCE** (see `compose-envelope` CLI; validation + JSON + stub result preview). No request submission implemented yet.
- HTML: view-only (stats, graphs, readouts, exports + static envelope previews).
All surfaces use only the read surface (GET).

**Future target (TUI only):** operator request/input surface (submitting composed envelopes/intents via a future gated Engine command API). Engine (and capabilities) own execution, decisions, gates, receipts. TUI must never directly execute capabilities, mutate engine state, bypass gates, write receipts, or self-approve. Compose/preview here is local preparation only.

**HTML role (permanent for this surface in repo):** view-only telemetry/stats/graphs/readouts/exports (includes static previews of composed envelopes).

## What This Is (Current Scaffold)

- A minimal Python package providing a read-only client + TUI (read/render observation + **local compose/preview of ACT-MCE Engine Command Envelopes**) + HTML (view-only) export.
- Strictly GET-only client against the read surface `http://127.0.0.1:8765` (configurable). No write verbs in this repo.
- Designed so the TUI (future: operator request/input surface) and the HTML (view-only stats/graphs/readouts) are pure consumers of the read surface today. TUI can locally compose/preview envelopes (for future gated submit); TUI never owns execution. Command submission (if any) will be gated through future Engine API; TUI never owns execution.

## Quick Start

```bash
# Install in editable mode (with optional TUI support when available)
python3 -m pip install -e ".[dev]"

# Use the client directly
python3 -c '
from act_tui_html_hybrid import ReadSurfaceClient
c = ReadSurfaceClient()
print(c.health())
print(c.run_current())
'
```

Start the ACT-MCE read server (from the ACT-MCE repo) first:
```bash
python3 -m act_viewer_server.read_server
```

## Implemented Surfaces (Current Scaffold Phase)

- `ReadSurfaceClient` — health, run_current, run_stats, events, receipts, gates, traces, warnings. All GET only for live. `load_fixture` / `get_snapshot_from_fixture` for offline preview (separate from live paths). No mutation or write paths.
- `ACTHybridViewerTUI` — refined console with boxes, ANSI status, full sections, prominent OFFLINE and SAMPLE PREVIEW banners + **local Engine Command Envelope composer/previewer** (compose via CLI or methods; shows in render; validates locally; stub results only). **Current: read/render + local compose/preview. No execute, approve, advance, or request submission actions or keys. (Future target role: gated operator request/input surface.)**
- `render_read_only_html` / `export_html_to_file` — improved static self-contained HTML (tables, cards, badges, dark theme, preview banners + static Engine Command Envelope preview section). View-only permanently in this repo (stats, graphs, readouts, exports). Zero forms, zero mutating scripts, zero active elements.
- CLI mains for `tui` and `html_export` modules (and console scripts) — expose only read/show/render + local `compose-envelope` (preview only) subcommands today.

## Package Layout

```
act_tui_html_hybrid/
  __init__.py
  read_surface_client.py
  tui.py
  html_export.py
docs/
  BOUNDARY.md
  READ_SURFACE_CONTRACT.md
tests/
  fixtures/
    sample_snapshot.json   # marked SAMPLE_FIXTURE_PREVIEW_ONLY
pyproject.toml
README.md
```

## Forbidden (Enforced by Tests and Contract)

**Permanent (never in this repo):**
- No POST, PUT, PATCH, DELETE.
- No direct command execution, shell, PTY, or capability calls/invocation.
- No approval workflow, phase advancement, gate bypass, writing receipts, or mutating ACT-MCE state directly.
- No importing ACT-MCE engine/gate/capability/registry/execution/mutation modules.
- No claiming readiness, approval, acceptance, or final operator sign-off (those come from engine gate results only).
- TUI must never directly execute capabilities, mutate engine state, bypass gates, write receipts, or self-approve.

**Current scaffold (this phase — no request submission implemented yet):**
- TUI and HTML must not expose or implement mutation actions, command submission, or real input surfaces. CLI and surfaces are read/render (TUI) / view-only (HTML) only. **Local compose/preview of envelopes is supported** (for operator awareness; no submit/exec).
- All surfaces consume the read surface only. Compose is local data only.

## Running Tests

```bash
python3 -m pytest -q
```

All tests must pass. They verify the required Phase 2 + original contract items (current scaffold posture + permanent boundaries):
- TUI renders sample state without server (via fixture) — current read/render posture.
- HTML export creates static file from fixture — view-only.
- HTML contains no forms.
- HTML contains no mutating scripts.
- CLI does not expose execute/approve/advance *or command submission* commands (only read/show/render + local `compose-envelope` for preview).
- Source contains no ACT-MCE engine/gate/capability imports.
- Client still uses only GET (live paths).
- Server unavailable path is graceful.
- Plus: fixtures marked preview, docs distinguish current read-only scaffold + local envelope compose/preview vs. future gated TUI request/input role (HTML view-only), no impl of request surfaces/exec yet, improved layouts respect boundary, new compose tests cover validation/no-exec/no-mutate, etc.

## Phase 2+: Visual / Readability Refinement + Local Engine Command Envelope Compose/Preview (Current Scaffold)

- Improved console TUI layout with boxes, status colors (ANSI), clear OFFLINE / SAMPLE PREVIEW banners, full sections (events, traces, etc.). **Current: read/render-only surface + local compose/preview of ACT-MCE Engine Command Envelopes** (new `compose-envelope` CLI + methods; local validation + JSON/stub preview; appears in render).
- Improved self-contained static HTML with modern dark theme, tables, cards, badges, prominent preview warnings + **static Engine Command Envelope preview section** (view-only). **HTML: view-only (stats/graphs/readouts/exports + static envelope previews) for this repo.**
- Sample fixture dataset at `tests/fixtures/sample_snapshot.json` (explicitly marked `SAMPLE_FIXTURE_PREVIEW_ONLY`).
- CLI entrypoints (read + render + local compose/preview only; no command submission):
  - `python -m act_tui_html_hybrid.tui --base-url http://127.0.0.1:8765`
  - `python -m act_tui_html_hybrid.tui show-health`
  - `python -m act_tui_html_hybrid.tui compose-envelope --type list_wrappers --dry-run`
  - `python -m act_tui_html_hybrid.tui show-current --fixture tests/fixtures/sample_snapshot.json`
  - `python -m act_tui_html_hybrid.html_export --out dist/snapshot.html`
  - `python -m act_tui_html_hybrid.html_export --fixture tests/fixtures/sample_snapshot.json --out /tmp/preview.html`
- After `pip install -e .` you can also use the scripts: `act-tui-viewer` and `act-html-export`.
- All current commands are read/render (TUI) / view (HTML) + local compose/preview only. Unavailable server → clear offline state. Fixtures for preview only. Compose is 100% local.

**Note on future:** Later phases may add TUI request submission *through a gated Engine command API only* (using envelopes composed here). This repo will never implement direct execution, direct mutation, or ungated writes. HTML stays view-only. TUI compose/preview is preparation only.

## Usage with Live Read Surface

Start the upstream ACT-MCE read server first (from ACT-MCE repo), then:

```bash
python -m act_tui_html_hybrid.tui
# or with specific
python -m act_tui_html_hybrid.tui --base-url http://127.0.0.1:8765 show-current
```

## Offline / Preview with Fixture

```bash
python -m act_tui_html_hybrid.tui --fixture tests/fixtures/sample_snapshot.json
python -m act_tui_html_hybrid.html_export --fixture tests/fixtures/sample_snapshot.json --out dist/sample.html
```

The fixture is synthetic preview data only. It simulates a BLOCKED Stage 1 state with sample receipts/gates/warnings/events for layout testing. Never treat as live truth.

**Current implementation note:** TUI/CLI surfaces here are read/render-only + local compose/preview of Engine Command Envelopes (no request submission code paths exist). Compose produces local validated previews + stub results only. Future gated request support (if added) will be clearly separated and will never allow direct engine mutation or bypass. HTML export includes static view-only envelope preview examples.

## Status

Phase 2+ complete. **Current state: read/render-only TUI scaffold + local compose/preview of Engine Command Envelopes + view-only HTML.** No command/input/request submission implemented (CLI supports show-*/render + `compose-envelope` for local preview only).

**TUI compose/preview:** Local only (builds CommandEnvelope, validates against known types, shows pretty JSON + stub preview result in render/CLI/HTML). Prepares for future gated submit; does not submit or execute.

**Future target (TUI role):** operator request/input surface that submits (composed) envelopes to a *gated Engine command API*. Engine owns execution/gates/receipts/decisions. Capabilities perform bounded work. TUI never directly executes, mutates, bypasses, or claims acceptance.

**HTML:** view-only permanently (in this repo's HTML surface; includes static envelope preview examples).

Future phases (full Textual App, live updates, gated request relay) must continue to obey the hard permanent boundaries.

See:
- docs/BOUNDARY.md
- docs/READ_SURFACE_CONTRACT.md

Operator review of engine-owned gate results and receipts remains the final authority. Fixtures and rendered outputs (including envelope previews) from this viewer are for awareness and development only.
