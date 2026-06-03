"""
act_tui_html_hybrid

ACT TUI/HTML Hybrid viewer (current: read/render observation + LOCAL compose/preview of Engine Command Envelopes + view-only HTML).

**Current:** 
- TUI: read/render-only state observation + local compose/preview of ACT-MCE Engine Command Envelopes (for future gated submission).
- HTML: view-only (stats/graphs/readouts/exports + static envelope previews).
- Consumes only the ACT-MCE localhost read surface via GET (no writes).

**Future target (TUI only):** operator request/input surface via gated Engine command API only (compose here prepares; submit is future, outside this repo).

**Permanent (never):**
- TUI/HTML must never directly execute capabilities, mutate engine state, bypass gates, write receipts, or self-approve.
- Never import ACT-MCE engine/gate/capability/registry/execution/mutation modules.
- No real submission/execution from this surface (compose/preview is local only).

Core rule:
  The viewer observes (and locally composes envelopes for preview). The engine decides. Gates decide advancement.
  Operator acceptance remains final.

This package MUST NOT import ACT-MCE engine, gate, capability,
registry, execution, or mutation modules.

All live client operations are GET only. Compose/preview is purely local (no network, no mutation).
"""

from .read_surface_client import ReadSurfaceClient
from .tui import ACTHybridViewerTUI
from .html_export import render_read_only_html, export_html_to_file
from .command_envelope import (
    CommandEnvelope,
    CommandResult,
    CommandType,
    KNOWN_COMMAND_TYPES,
    preview_envelope,
)

__all__ = [
    "ReadSurfaceClient",
    "ACTHybridViewerTUI",
    "render_read_only_html",
    "export_html_to_file",
    "CommandEnvelope",
    "CommandResult",
    "CommandType",
    "KNOWN_COMMAND_TYPES",
    "preview_envelope",
]

__version__ = "0.0.3"
