# act-tui-html-hybrid

**ACT TUI/HTML Hybrid viewer scaffold** — a separate observation lane for ACT-MCE.

This repository consumes **only** the ACT-MCE localhost read surface. It must never import ACT-MCE engine, gate, capability, registry, execution, or mutation modules.

## Core Rule

> The viewer observes. The engine decides. Gates decide advancement. Operator acceptance remains final.

## What This Is

- A minimal Python package providing a read-only client + TUI placeholder + HTML export placeholder.
- Strictly GET-only against `http://127.0.0.1:8765` (configurable).
- Designed so the Textual TUI owns operator cockpit surfaces and the HTML owns telemetry visualization — both as pure consumers.

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

## Implemented Surfaces (Scaffold)

- `ReadSurfaceClient` — health, run_current, run_stats, events, receipts, gates, traces, warnings. All GET. Graceful unavailable handling.
- `ACTHybridViewerTUI` — minimal console placeholder. Shows connection status and sections. **No execute, approve, or advance actions.**
- `render_read_only_html` / `export_html_to_file` — produces static, self-contained HTML from snapshot data. Read-only. Zero forms, zero scripts that mutate.

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
pyproject.toml
README.md
```

## Forbidden (Enforced by Tests and Contract)

- No POST, PUT, PATCH, DELETE.
- No command execution, shell, PTY, or capability calls.
- No approval workflow, phase advancement, or writing receipts.
- No mutating ACT-MCE state.
- No importing ACT-MCE engine/gate/capability modules.
- No claiming readiness, approval, or acceptance (those come from engine gate results only).
- TUI and HTML must not expose or implement mutation actions.

## Running Tests

```bash
python3 -m pytest -q
```

All tests must pass. They verify:
1. Client only uses GET.
2. Client handles server unavailable gracefully.
3. No forbidden imports in source.
4. No mutation verbs appear as implemented routes/actions.
5. TUI does not expose execute/approve/advance actions.
6. HTML export is read-only.
7. README states this is an observation surface only.

## Status

Initial scaffold only. Full live polling, request submission relay, textual App integration, and rich HTML dashboards are future phases and must still respect the boundary.

See:
- docs/BOUNDARY.md
- docs/READ_SURFACE_CONTRACT.md

Operator review of engine-owned gate results and receipts remains the final authority.
