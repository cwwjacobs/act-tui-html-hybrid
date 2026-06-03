"""
Phase 2 static HTML export for ACT TUI/HTML Hybrid viewer (refined visual/readability).

Renders improved, static, self-contained HTML from read-surface data or sample fixtures.
**HTML role (permanent for this repo surface):** view-only stats, graphs, readouts, exports.

Zero forms, zero scripts that mutate or phone home, zero active controls.

The viewer observes (HTML view-only). The engine decides. Gates decide advancement.
Operator acceptance remains final.
"""

from __future__ import annotations

import argparse
import html as html_module
import json
import sys
from pathlib import Path
from typing import Any, Dict

from .read_surface_client import ReadSurfaceClient


def render_read_only_html(snapshot: Dict[str, Any] | None = None, title: str = "ACT Viewer Hybrid - Read Only Snapshot", fixture_note: str | None = None) -> str:
    """Return a complete, self-contained, improved HTML document for the provided snapshot.

    If snapshot is None, a fresh read will be attempted (still read-only).
    The output contains zero executable paths, zero mutation affordances, zero forms, zero scripts.
    Supports explicit fixture_note for SAMPLE PREVIEW banners.
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
    evs = snapshot.get("events", {}).get("events", []) if "events" in snapshot else []
    meta = snapshot.get("_meta", {})

    is_preview = "SAMPLE_FIXTURE_PREVIEW_ONLY" in str(meta) or bool(fixture_note)
    preview_banner = ""
    if is_preview:
        note = fixture_note or meta.get("note", "SAMPLE PREVIEW DATA — LAYOUT / OFFLINE TESTING ONLY")
        preview_banner = f"""
  <div class="preview-banner">
    <strong>⚠ SAMPLE / FIXTURE PREVIEW DATA ONLY</strong><br>
    {esc(note)}<br>
    <span class="meta">This HTML does not reflect live engine state, gate results, or receipts. For viewer development and readability testing only.</span>
  </div>
"""

    conn = "CONNECTED (read-only)" if health.get("status") == "OK" and not health.get("error") else f"OFFLINE / UNAVAILABLE: {health.get('error', 'n/a')}"
    conn_class = "ok" if "CONNECTED" in conn and "OFFLINE" not in conn else "disconnected"

    # Build nicer HTML with tables, cards, badges
    def make_badge(text: str, cls: str = "badge") -> str:
        return f'<span class="{cls}">{esc(text)}</span>'

    def make_table(rows: list[tuple[str, str]], headers: tuple[str, str] = ("Key", "Value")) -> str:
        if not rows:
            return "<p class='empty'>(none)</p>"
        h = "".join(f"<th>{esc(hh)}</th>" for hh in headers)
        r = "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in rows)
        return f"<table><thead><tr>{h}</tr></thead><tbody>{r}</tbody></table>"

    # receipts as list
    rec_html = ""
    if recs:
        for r in recs:
            rec_html += f"""
      <div class="card">
        <div class="card-head">{esc(r.get('receipt_id', '?'))} {make_badge(r.get('status_claim', ''), 'badge status')}</div>
        <div class="card-body">{esc(r.get('summary', ''))}</div>
        <div class="meta">type: {esc(r.get('receipt_type', ''))}</div>
      </div>"""
    else:
        rec_html = "<p class='empty'>(none — engine gate result pending or missing in source data)</p>"

    gate_html = ""
    if gts:
        for g in gts:
            blockers = ", ".join(map(str, g.get("blockers", []))) if g.get("blockers") else "—"
            gate_html += f"""
      <div class="card gate-{esc(str(g.get('status','')).lower())}">
        <div class="card-head">{esc(g.get('gate_id', '?'))} {make_badge(esc(g.get('status', '?')), 'badge')}</div>
        <div class="card-body">{esc(g.get('summary', ''))}</div>
        <div class="meta">blockers: {esc(blockers)}</div>
      </div>"""
    else:
        gate_html = "<p class='empty'>(none)</p>"

    warn_html = ""
    if warns:
        for w in warns:
            warn_html += f'<div class="warn-item">⚠ [{esc(w.get("severity","WARN"))}] {esc(w.get("message",""))}</div>'
    else:
        warn_html = "<p class='empty'>(none)</p>"

    ev_html = ""
    if evs:
        for e in evs[:8]:
            ev_html += f"<li>{esc(e.get('ts','')[:19])} — <strong>{esc(e.get('type',''))}</strong>: {esc(str(e.get('message',''))[:80])}</li>"
        ev_html = f"<ul class='event-list'>{ev_html}</ul>"
    else:
        ev_html = "<p class='empty'>(no events surfaced in this snapshot)</p>"

    # stats table data
    counts = stats.get("counts", {})
    stats_rows = [
        ("events", str(counts.get("events", 0))),
        ("receipts", str(counts.get("receipts", 0))),
        ("gates", str(counts.get("gates", 0))),
        ("traces", str(counts.get("traces", 0))),
        ("warnings", str(counts.get("warnings", 0))),
    ]

    run_rows = [
        ("run_id", rc.get("run_id", "n/a")),
        ("admission_stage", rc.get("admission_stage", "n/a")),
        ("stage_id / phase_id", f"{rc.get('stage_id', 'n/a')} / {rc.get('phase_id', 'n/a')}"),
        ("status", rc.get("status", "n/a")),
        ("source", rc.get("source", "n/a")),
    ]
    snap_meta = (rc.get("viewer_snapshot", {}) or {}).get("metadata", {})
    if snap_meta:
        run_rows += [
            ("stage_1_ready (from engine)", str(snap_meta.get("stage_1_ready", False))),
            ("stage_2_allowed (from engine)", str(snap_meta.get("stage_2_allowed", False))),
        ]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    :root {{ color-scheme: dark; }}
    body {{ font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 1.5rem auto; max-width: 980px; background: #0b0f14; color: #e6edf3; line-height: 1.5; padding: 0 1rem; }}
    h1, h2, h3 {{ color: #58a6ff; margin: 0.3em 0; }}
    .header {{ border-bottom: 2px solid #30363d; padding-bottom: 1rem; margin-bottom: 1rem; }}
    .preview-banner {{ background: #3d2a00; border: 2px solid #d29922; color: #f0b429; padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem; font-size: 0.95rem; }}
    .section {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1.25rem; }}
    .status {{ padding: 0.35rem 0.85rem; border-radius: 999px; display: inline-block; font-size: 0.9rem; font-weight: 600; }}
    .ok {{ background: #0f5132; color: #75b798; border: 1px solid #198754; }}
    .disconnected {{ background: #5c2a2a; color: #f87171; border: 1px solid #b91c1c; }}
    .meta, .empty {{ font-size: 0.82rem; color: #8b949e; }}
    .empty {{ font-style: italic; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ text-align: left; padding: 0.35rem 0.5rem; border-bottom: 1px solid #30363d; }}
    th {{ color: #58a6ff; font-weight: 600; }}
    .card {{ background: #0b0f14; border: 1px solid #30363d; border-radius: 6px; padding: 0.6rem 0.8rem; margin: 0.4rem 0; }}
    .card-head {{ font-weight: 600; margin-bottom: 0.2rem; display: flex; gap: 0.5rem; align-items: center; }}
    .card-body {{ font-size: 0.9rem; color: #c9d1d9; }}
    .badge {{ font-size: 0.75rem; padding: 0.1rem 0.5rem; border-radius: 4px; background: #21262d; border: 1px solid #30363d; }}
    .badge.status {{ background: #1f6feb; color: white; }}
    .gate-blocked .badge {{ background: #b91c1c; color: white; }}
    .gate-unknown .badge {{ background: #6b7280; color: white; }}
    .warn-item {{ background: #2d1f00; border-left: 4px solid #d29922; padding: 0.3rem 0.6rem; margin: 0.25rem 0; font-size: 0.9rem; }}
    .event-list {{ margin: 0; padding-left: 1.2rem; font-size: 0.85rem; }}
    .event-list li {{ margin: 0.15rem 0; }}
    .footer {{ margin-top: 2rem; font-size: 0.78rem; color: #6e7681; border-top: 1px solid #30363d; padding-top: 0.75rem; }}
    .footer strong {{ color: #8b949e; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
    @media (max-width: 700px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="header">
    <h1>ACT TUI/HTML Hybrid — Read-Only Snapshot</h1>
    <p class="meta">Static export • observation surface only • no active controls, forms, or mutation paths • generated via read-surface client (GET only)</p>
  </div>

  {preview_banner}

  <div class="section">
    <h2>Connection Status</h2>
    <div class="status {conn_class}">{esc(conn)}</div>
    <div class="meta" style="margin-top:0.5rem">Base / source: {esc(health.get('source') or snapshot.get('health',{}).get('source','n/a'))} • Client uses only GET against read surface. {esc(health.get('service',''))}</div>
  </div>

  <div class="two-col">
    <div class="section">
      <h2>Run Current</h2>
      {make_table(run_rows)}
    </div>
    <div class="section">
      <h2>Stats</h2>
      {make_table(stats_rows)}
    </div>
  </div>

  <div class="section">
    <h2>Receipts (engine-owned only)</h2>
    {rec_html}
  </div>

  <div class="section">
    <h2>Gates (engine-owned only)</h2>
    {gate_html}
  </div>

  <div class="two-col">
    <div class="section">
      <h2>Warnings</h2>
      {warn_html}
    </div>
    <div class="section">
      <h2>Events (read-only telemetry)</h2>
      {ev_html}
    </div>
  </div>

  <div class="section">
    <h2>Traces</h2>
    <p class="meta">Traces: {len(snapshot.get('traces',{}).get('traces', []))} — full trace details available via dedicated viewer or export in engine-controlled flows.</p>
  </div>

  <div class="footer">
    <strong>BOUNDARY ENFORCED</strong>: The viewer observes. The engine decides. Gates decide advancement. Operator acceptance remains final.<br>
    Generated from read-surface data / fixture only. <strong>No POST, no shell, no mutation, no ACT-MCE engine/gate/capability imports, no approval workflow.</strong><br>
    Fixture/sample data (when present) is explicitly marked PREVIEW ONLY and must not be treated as authoritative.
  </div>
</body>
</html>
"""
    return html


def export_html_to_file(path: str, snapshot: Dict[str, Any] | None = None, fixture_note: str | None = None) -> str:
    """Write the read-only HTML to a file and return the path. Pure side-effect free except FS write of static content."""
    content = render_read_only_html(snapshot, fixture_note=fixture_note)
    outp = Path(path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(content, encoding="utf-8")
    return str(outp)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for python -m act_tui_html_hybrid.html_export

    Only reads (live or --fixture) and renders static self-contained HTML.
    Example:
      python -m act_tui_html_hybrid.html_export --out dist/preview.html
      python -m act_tui_html_hybrid.html_export --fixture tests/fixtures/sample_snapshot.json --out /tmp/sample.html
    """
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="act_tui_html_hybrid.html_export",
        description="ACT TUI/HTML Hybrid static HTML renderer (Phase 2). Read-only. Produces self-contained HTML with no forms or scripts.",
    )
    parser.add_argument("--base-url", default=ReadSurfaceClient.DEFAULT_BASE_URL,
                        help="Read surface base (used only if no --fixture)")
    parser.add_argument("--fixture", default=None,
                        help="Sample fixture JSON (PREVIEW ONLY) to render instead of live read")
    parser.add_argument("--out", default="dist/act_viewer_snapshot.html",
                        help="Output path for the static HTML file (default: %(default)s)")
    parser.add_argument("--title", default="ACT Viewer Hybrid - Read Only Snapshot (Phase 2)",
                        help="HTML document title")
    args = parser.parse_args(argv)

    client = ReadSurfaceClient(base_url=args.base_url)
    snap: Dict[str, Any] | None = None
    f_note = None
    if args.fixture:
        loaded = client.get_snapshot_from_fixture(args.fixture)
        if "error" in loaded:
            print(f"ERROR loading fixture: {loaded['error']}", file=sys.stderr)
            return 2
        snap = loaded
        meta = loaded.get("_meta", {})
        f_note = meta.get("note", "Loaded from fixture for preview")
    else:
        snap = client.fetch_snapshot()

    out_path = export_html_to_file(args.out, snap, fixture_note=f_note)
    print(f"Wrote static read-only HTML to: {out_path}")
    print("Open the file in a browser. It contains no active elements or write paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
