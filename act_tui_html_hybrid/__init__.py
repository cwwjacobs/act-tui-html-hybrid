"""
act_tui_html_hybrid

ACT TUI/HTML Hybrid viewer scaffold.

Strictly an observation surface for the ACT-MCE localhost read surface.

Core rule:
  The viewer observes. The engine decides. Gates decide advancement.
  Operator acceptance remains final.

This package MUST NOT import ACT-MCE engine, gate, capability,
registry, execution, or mutation modules.

All client operations are GET only. No mutation verbs are implemented.
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

__version__ = "0.0.1"
