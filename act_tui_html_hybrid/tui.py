"""
Minimal TUI placeholder for ACT TUI/HTML Hybrid viewer.

Displays connection status and key read-only sections from the read surface.
This is strictly an observation surface.

The viewer observes. The engine decides. Gates decide advancement.
Operator acceptance remains final.

Forbidden in this module:
- No execute, approve, advance, run, mutate actions exposed.
- All display and refresh are read-only.
- Uses only the ReadSurfaceClient (GET only).
"""

from __future__ import annotations

from typing import Any, Dict

from .read_surface_client import ReadSurfaceClient


class ACTHybridViewerTUI:
    """Placeholder TUI surface.

    Renders a textual (console) view of read-surface data.
    No command execution, no approval workflow, no phase advancement.
    """

    def __init__(self, client: ReadSurfaceClient | None = None):
        self.client = client or ReadSurfaceClient()
        self._last_snapshot: Dict[str, Any] = {}
        self._connected = False

    def refresh(self) -> Dict[str, Any]:
        """Pull fresh read-only data. Never mutates."""
        snapshot = self.client.fetch_snapshot()
        self._last_snapshot = snapshot
        health = snapshot.get("health", {})
        self._connected = health.get("status") == "OK" and not health.get("error")
        return snapshot

    def get_connection_status(self) -> str:
        """Human readable connection status for display."""
        if not self._last_snapshot:
            return "UNKNOWN (no refresh yet)"
        health = self._last_snapshot.get("health", {})
        if health.get("error"):
            return f"DISCONNECTED: {health.get('error')}"
        if health.get("status") == "OK" and health.get("read_only"):
            return "CONNECTED (read-only)"
        return "CONNECTED (limited)"

    def render(self) -> str:
        """Return a console-renderable string of current sections. Read-only only."""
        lines = []
        lines.append("=== ACT TUI/HTML Hybrid Viewer (PLACEHOLDER) ===")
        lines.append(f"Connection: {self.get_connection_status()}")
        lines.append("Base URL: " + self.client.base_url)
        lines.append("")
        lines.append("--- RUN CURRENT ---")
        rc = self._last_snapshot.get("run_current", {})
        lines.append(f"  run_id: {rc.get('run_id', 'n/a')}")
        lines.append(f"  admission_stage: {rc.get('admission_stage', 'n/a')}")
        lines.append(f"  status: {rc.get('status', 'n/a')}")
        lines.append(f"  source: {rc.get('source', 'n/a')}")
        snap = rc.get("viewer_snapshot", {})
        if snap:
            lines.append(f"  stage_1_ready: {snap.get('metadata', {}).get('stage_1_ready')}")
            lines.append(f"  stage_2_allowed: {snap.get('metadata', {}).get('stage_2_allowed')}")
        lines.append("")
        lines.append("--- STATS ---")
        stats = self._last_snapshot.get("stats", {})
        counts = stats.get("counts", {})
        lines.append(f"  receipts: {counts.get('receipts', 0)} gates: {counts.get('gates', 0)} warnings: {counts.get('warnings', 0)}")
        lines.append("")
        lines.append("--- RECEIPTS (engine-owned) ---")
        recs = self._last_snapshot.get("receipts", {}).get("receipts", [])
        if recs:
            for r in recs[:3]:
                lines.append(f"  - {r.get('receipt_id')}: {r.get('status_claim')}")
        else:
            lines.append("  (none or pending engine gate)")
        lines.append("")
        lines.append("--- GATES (engine-owned) ---")
        gts = self._last_snapshot.get("gates", {}).get("gates", [])
        if gts:
            for g in gts[:3]:
                lines.append(f"  - {g.get('gate_id')}: {g.get('status')}")
                if g.get("blockers"):
                    lines.append(f"    blockers: {g.get('blockers')}")
        else:
            lines.append("  (none)")
        lines.append("")
        lines.append("--- WARNINGS ---")
        warns = self._last_snapshot.get("warnings", {}).get("warnings", [])
        if warns:
            for w in warns[:5]:
                lines.append(f"  ! {w.get('message')}")
        else:
            lines.append("  (none)")
        lines.append("")
        lines.append("--- KEYS (placeholder, read-only) ---")
        lines.append("  [r] refresh (read)   [q] quit")
        lines.append("  (No execute / approve / advance keys are present.)")
        lines.append("")
        lines.append("This surface OBSERVES only. Engine decides. Operator acceptance is final.")
        return "\n".join(lines)

    def run(self, auto_refresh: bool = True) -> None:
        """Run a single-pass placeholder render loop (blocking until 'q' in real TUI).

        For this scaffold this is a one-shot display for demo / test.
        A real textual app would use App.run() with live polling.
        """
        if auto_refresh:
            self.refresh()
        print(self.render())
        print("\n(Placeholder TUI exited. In a full TUI this would be interactive but read-only.)")

    # Explicitly no mutation surfaces
    # Intentionally omitted: execute, approve, advance, request_run, mutate, etc.
