"""
Minimal HTML export placeholder for ACT TUI/HTML Hybrid viewer.

Renders a static, read-only snapshot of read-surface data as self-contained HTML.
No scripts that call back with mutations, no forms that POST, no active controls.

The viewer observes. The engine decides. Gates decide advancement.
Operator acceptance remains final.
"""

from __future__ import annotations

import html as html_module
from typing import Any, Dict

from .read_surface_client import ReadSurfaceClient


def render_read_only_html(snapshot: Dict[str, Any] | None = None, title: str = "ACT Viewer Hybrid - Read Only Snapshot") -> str:
    """Return a complete, self-contained HTML document for the provided snapshot.

    If snapshot is None, a fresh read will be attempted (still read-only).
    The output contains zero executable paths, zero mutation affordances.
    """
    if snapshot is None:
        client = ReadSurfaceClient()
        snapshot = client.fetch_snapshot()

    # Escape for safety
    def esc(v: Any) -> str:
        return html_module.escape(str(v)) if v is not None else ""

    health = snapshot.get("health", {})
    rc = snapshot.get("run_current", {})
    stats = snapshot.get("stats", {})
    recs = snapshot.get("receipts", {}).get("receipts", [])
    gts = snapshot.get("gates", {}).get("gates", [])
    warns = snapshot.get("warnings", {}).get("warnings", [])

    conn = "CONNECTED (read-only)" if health.get("status") == "OK" and not health.get("error") else f"DISCONNECTED: {health.get('error', 'n/a')}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #0b0f14; color: #e6edf3; }}
    h1, h2 {{ color: #58a6ff; }}
    .section {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; }}
    .status {{ padding: 0.5rem 1rem; border-radius: 4px; display: inline-block; }}
    .ok {{ background: #0f5132; color: #75b798; }}
    .disconnected {{ background: #5c2a2a; color: #f87171; }}
    pre {{ background: #0b0f14; padding: 0.5rem; overflow: auto; border: 1px solid #30363d; }}
    .warning {{ color: #f0b429; }}
    .meta {{ font-size: 0.85rem; color: #8b949e; }}
    .footer {{ margin-top: 2rem; font-size: 0.8rem; color: #6e7681; border-top: 1px solid #30363d; padding-top: 1rem; }}
  </style>
</head>
<body>
  <h1>ACT TUI/HTML Hybrid — Read-Only Snapshot</h1>
  <p class="meta">This page is a static export. It contains no active controls, no execution, and no write paths.</p>

  <div class="section">
    <h2>Connection</h2>
    <div class="status {'ok' if 'CONNECTED' in conn else 'disconnected'}">{esc(conn)}</div>
    <div class="meta">Base: {esc(snapshot.get('health', {}).get('source', 'n/a'))} | Client observes only via GET</div>
  </div>

  <div class="section">
    <h2>Run Current</h2>
    <pre>run_id: {esc(rc.get('run_id'))}
admission_stage: {esc(rc.get('admission_stage'))}
status: {esc(rc.get('status'))}
source: {esc(rc.get('source'))}</pre>
  </div>

  <div class="section">
    <h2>Stats</h2>
    <pre>receipts: {esc(stats.get('counts', {}).get('receipts', 0))}
gates: {esc(stats.get('counts', {}).get('gates', 0))}
warnings: {esc(stats.get('counts', {}).get('warnings', 0))}</pre>
  </div>

  <div class="section">
    <h2>Receipts (engine-owned only)</h2>
    {"".join(f"<pre>{esc(r)}</pre>" for r in recs) if recs else "<p>(none — engine gate result pending or missing)</p>"}
  </div>

  <div class="section">
    <h2>Gates (engine-owned only)</h2>
    {"".join(f"<pre>gate: {esc(g.get('gate_id'))} status: {esc(g.get('status'))} blockers: {esc(g.get('blockers'))}</pre>" for g in gts) if gts else "<p>(none)</p>"}
  </div>

  <div class="section">
    <h2>Warnings</h2>
    {"".join(f"<div class='warning'>⚠ {esc(w.get('message'))}</div>" for w in warns) if warns else "<p>(none)</p>"}
  </div>

  <div class="footer">
    <strong>BOUNDARY</strong>: The viewer observes. The engine decides. Gates decide advancement. Operator acceptance remains final.<br>
    This HTML is generated from read-surface data only. No POST, no shell, no mutation, no ACT-MCE engine imported.
  </div>
</body>
</html>
"""
    return html


def export_html_to_file(path: str, snapshot: Dict[str, Any] | None = None) -> str:
    """Write the read-only HTML to a file and return the path."""
    content = render_read_only_html(snapshot)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
