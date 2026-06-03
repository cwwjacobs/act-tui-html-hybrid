"""
act_tui_html_hybrid

ACT TUI/HTML Hybrid viewer scaffold (current phase: read/render-only TUI + view-only HTML).

**Current scaffold:** TUI is read/render-only (no request submission implemented). HTML is view-only (stats/graphs/readouts/exports). Consumes only the ACT-MCE localhost read surface via GET.

**Future target (TUI):** operator request/input surface via gated Engine command API only.

**Permanent:** TUI/HTML must never directly execute capabilities, mutate engine state, bypass gates, write receipts, or self-approve. Never import ACT-MCE engine/gate/capability modules.

Core rule:
  The viewer observes. The engine decides. Gates decide advancement.
  Operator acceptance remains final.

This package MUST NOT import ACT-MCE engine, gate, capability,
registry, execution, or mutation modules.

All client operations (live) are GET only. No mutation verbs, no request submission, no command surfaces implemented in this scaffold.
"""

from .read_surface_client import ReadSurfaceClient
from .tui import ACTHybridViewerTUI
from .html_export import render_read_only_html, export_html_to_file

__all__ = [
    "ReadSurfaceClient",
    "ACTHybridViewerTUI",
    "render_read_only_html",
    "export_html_to_file",
]

__version__ = "0.0.2"
