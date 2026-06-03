"""
Phase 2 TUI for ACT TUI/HTML Hybrid viewer (refined visual/readability; current scaffold).

**Current scaffold phase:** Displays improved layout of read/render-only sections from the read surface or sample fixtures.
TUI here is read/render-only. Clear unavailable/offline states. No request submission implemented.

**Future target role for TUI:** operator request/input surface (gated Engine command API only; not in this repo/phase).

The viewer observes (current). The engine decides. Gates decide advancement.
Operator acceptance remains final.

Forbidden in this module (permanent + current):
- No execute, approve, advance, run, mutate actions exposed.
- No direct execution/mutation/gate bypass/receipt writing/self-approve (ever).
- All display and refresh are read-only (current posture).
- Uses only the ReadSurfaceClient (GET only) or fixture loads (preview).
- No cockpit/control language or command submission (current; future gated requests only, never direct).
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from .read_surface_client import ReadSurfaceClient


class ACTHybridViewerTUI:
    """Phase 2 refined TUI surface for visual/readability.

    Renders improved console layout of read-surface data (or fixtures).
    No command execution, no approval workflow, no phase advancement.
    Always shows clear OFFLINE state when read surface unavailable.
    """

    # Simple ANSI for readability (no external deps)
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    BG_DARK = "\033[48;5;236m"  # subtle bg if supported

    def __init__(self, client: ReadSurfaceClient | None = None):
        self.client = client or ReadSurfaceClient()
        self._last_snapshot: Dict[str, Any] = {}
        self._connected = False
        self._offline = False
        self._fixture_used = False

    def refresh(self, fixture_path: str | None = None) -> Dict[str, Any]:
        """Pull fresh read-only data (or fixture). Never mutates. Sets clear offline flag."""
        if fixture_path:
            snapshot = self.client.get_snapshot_from_fixture(fixture_path)
            self._fixture_used = True
        else:
            snapshot = self.client.fetch_snapshot()
            self._fixture_used = False
        self._last_snapshot = snapshot
        health = snapshot.get("health", {})
        self._connected = bool(health.get("status") == "OK" and not health.get("error"))
        self._offline = not self._connected or bool(health.get("error")) or "unavailable" in str(health).lower()
        # Detect fixture
        meta = snapshot.get("_meta", {})
        if "SAMPLE_FIXTURE_PREVIEW_ONLY" in str(meta):
            self._fixture_used = True
        return snapshot

    def get_connection_status(self) -> str:
        """Human readable connection status for display. Always surfaces offline clearly."""
        if not self._last_snapshot:
            return "UNKNOWN (no refresh yet)"
        health = self._last_snapshot.get("health", {})
        meta = self._last_snapshot.get("_meta", {})
        if "SAMPLE_FIXTURE_PREVIEW_ONLY" in str(meta):
            return "OFFLINE (SAMPLE FIXTURE PREVIEW ONLY - no live server)"
        if health.get("error"):
            err = health.get("error", "")
            return f"OFFLINE / UNAVAILABLE: {err}"
        if health.get("status") == "OK" and health.get("read_only"):
            return "CONNECTED (read-only)"
        if self._offline:
            return "OFFLINE / READ SURFACE UNAVAILABLE"
        return "CONNECTED (limited)"

    def _c(self, text: str, color: str = "") -> str:
        """Wrap text with color if possible (tty friendly)."""
        if not color or not sys.stdout.isatty():
            return text
        return f"{color}{text}{self.RESET}"

    def _box(self, title: str, content_lines: list[str], width: int = 78) -> list[str]:
        """Simple box drawing for improved layout readability."""
        lines = []
        top = "┌" + "─" * (width - 2) + "┐"
        title_line = "│ " + self._c(title, self.BOLD + self.CYAN) + " " * (width - 3 - len(title)) + "│"
        lines.append(self._c(top, self.BLUE))
        lines.append(title_line)
        lines.append(self._c("├" + "─" * (width - 2) + "┤", self.BLUE))
        for cl in content_lines:
            # pad
            disp = cl[:width-4] if len(cl) > width-4 else cl + " " * (width-4 - len(cl))
            lines.append(self._c("│ ", self.BLUE) + disp + self._c(" │", self.BLUE))
        bot = "└" + "─" * (width - 2) + "┘"
        lines.append(self._c(bot, self.BLUE))
        return lines

    def render(self) -> str:
        """Return improved console-renderable layout. Always read-only. Clear offline/sample states."""
        lines: list[str] = []
        lines.append(self._c("╔" + "═" * 76 + "╗", self.BOLD + self.MAGENTA))
        lines.append(self._c("║  ACT TUI/HTML Hybrid Viewer  —  Phase 2 Visual Refinement (OBSERVE ONLY)  ║", self.BOLD + self.MAGENTA))
        lines.append(self._c("╚" + "═" * 76 + "╝", self.BOLD + self.MAGENTA))
        lines.append("")

        status = self.get_connection_status()
        color = self.GREEN if "CONNECTED" in status and "OFFLINE" not in status else (self.YELLOW if "SAMPLE" in status else self.RED)
        lines.append(self._c(f"  Status: {status}", color))
        if self._fixture_used:
            lines.append(self._c("  ⚠ USING SAMPLE FIXTURE DATA — PREVIEW / LAYOUT TESTING ONLY — NOT LIVE ENGINE STATE", self.YELLOW + self.BOLD))
        lines.append(self._c(f"  Base: {self.client.base_url}", self.DIM))
        lines.append("")

        # Offline banner if needed
        if self._offline or "OFFLINE" in status or "UNAVAILABLE" in status:
            banner = self._box(
                "⚠ READ SURFACE UNAVAILABLE / OFFLINE MODE",
                [
                    "The localhost ACT-MCE read server is not reachable or returned error.",
                    "Displaying any available partial data or fixture preview.",
                    "No execution, no advancement, no approval possible in this state.",
                    "Start the read server or use --fixture for preview.",
                ]
            )
            lines.extend(banner)
            lines.append("")

        # RUN CURRENT
        rc = self._last_snapshot.get("run_current", {})
        snap = rc.get("viewer_snapshot", {}) or {}
        run_lines = [
            f"run_id:           {rc.get('run_id', 'n/a')}",
            f"admission_stage:  {rc.get('admission_stage', 'n/a')}",
            f"stage / phase:    {rc.get('stage_id', 'n/a')} / {rc.get('phase_id', 'n/a')}",
            f"status:           {self._c(str(rc.get('status', 'n/a')), self.YELLOW if rc.get('status') != 'OK' else self.GREEN)}",
            f"source:           {rc.get('source', 'n/a')}",
        ]
        meta = snap.get("metadata", {}) if snap else {}
        if meta:
            run_lines.append(f"stage_1_ready:    {meta.get('stage_1_ready', False)}")
            run_lines.append(f"stage_2_allowed:  {meta.get('stage_2_allowed', False)}")
        lines.extend(self._box("RUN CURRENT (read-only snapshot)", run_lines))
        lines.append("")

        # STATS
        stats = self._last_snapshot.get("stats", {})
        counts = stats.get("counts", {})
        stats_lines = [
            f"events: {counts.get('events', 0):>4}   receipts: {counts.get('receipts', 0):>4}   gates: {counts.get('gates', 0):>4}",
            f"traces: {counts.get('traces', 0):>4}   warnings: {counts.get('warnings', 0):>4}",
        ]
        lines.extend(self._box("STATS (aggregate counts)", stats_lines))
        lines.append("")

        # RECEIPTS
        recs = self._last_snapshot.get("receipts", {}).get("receipts", [])
        rec_lines = []
        if recs:
            for r in recs[:5]:
                rec_lines.append(f"- {r.get('receipt_id', '?')}: {r.get('status_claim', '?')}  | {r.get('summary', '')[:50]}")
        else:
            rec_lines.append("(none or pending engine-owned receipt in current gate state)")
        lines.extend(self._box("RECEIPTS (engine-owned only)", rec_lines))
        lines.append("")

        # GATES
        gts = self._last_snapshot.get("gates", {}).get("gates", [])
        gate_lines = []
        if gts:
            for g in gts[:5]:
                stat_col = self.RED if str(g.get('status', '')).upper() in ("BLOCKED", "UNKNOWN") else self.GREEN
                gate_lines.append(f"- {g.get('gate_id', '?')}: {self._c(str(g.get('status', '?')), stat_col)}")
                if g.get("blockers"):
                    gate_lines.append(f"    blockers: {g.get('blockers')}")
                if g.get("summary"):
                    gate_lines.append(f"    {g.get('summary')[:70]}")
        else:
            gate_lines.append("(none)")
        lines.extend(self._box("GATES (engine-owned only)", gate_lines))
        lines.append("")

        # WARNINGS
        warns = self._last_snapshot.get("warnings", {}).get("warnings", [])
        warn_lines = []
        if warns:
            for w in warns[:6]:
                sev = w.get("severity", "WARN")
                col = self.RED if sev == "ERROR" else (self.YELLOW if sev == "WARN" else self.CYAN)
                warn_lines.append(f"[{sev}] {self._c(w.get('message', ''), col)}")
        else:
            warn_lines.append("(none)")
        lines.extend(self._box("WARNINGS (operator awareness)", warn_lines))
        lines.append("")

        # EVENTS (sample from fixture or live)
        evs = self._last_snapshot.get("events", {}).get("events", [])
        ev_lines = []
        if evs:
            for e in evs[:4]:
                ev_lines.append(f"{e.get('ts', '')[:19]} | {e.get('type', '')}: {str(e.get('message', ''))[:45]}")
        else:
            ev_lines.append("(no events in current read surface / fixture slice)")
        lines.extend(self._box("EVENTS (read-only telemetry)", ev_lines))
        lines.append("")

        # TRACES
        trs = self._last_snapshot.get("traces", {}).get("traces", [])
        tr_lines = [f"traces: {len(trs)} (see full export for details)" if trs else "(none in snapshot)"]
        lines.extend(self._box("TRACES", tr_lines))
        lines.append("")

        # Footer controls / boundary (no actions)
        lines.append(self._c("─" * 78, self.DIM))
        lines.append(self._c("KEYS (read-only placeholder): [r]efresh  [q]uit   |  No execute / approve / advance exposed.", self.DIM))
        lines.append(self._c("This surface OBSERVES only. Engine decides. Operator acceptance remains final.", self.BOLD))
        if self._fixture_used:
            lines.append(self._c("FIXTURE MODE: Sample data for preview. See _meta in data for provenance.", self.YELLOW))
        lines.append(self._c("─" * 78, self.DIM))
        return "\n".join(lines)

    def run(self, auto_refresh: bool = True, fixture_path: str | None = None) -> None:
        """Run a single-pass refined render (read-only)."""
        if auto_refresh:
            self.refresh(fixture_path=fixture_path)
        print(self.render())
        print(self._c("\n(Observation surface only. Single-pass placeholder. No controls for execution/approval/advancement.)", self.DIM))

    # Explicitly no mutation surfaces
    # Intentionally omitted: execute, approve, advance, request_run, mutate, etc.


def main(argv: list[str] | None = None) -> int:
    """CLI entry for python -m act_tui_html_hybrid.tui

    Supports read-only display commands only:
      (default)          full refined TUI render of current or fixture
      show-health        print health only
      show-current       print run_current snapshot
      show-stats         print stats
    All use --base-url or --fixture for offline preview.
    Never submits commands, never mutates.
    """
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="act_tui_html_hybrid.tui",
        description="ACT TUI/HTML Hybrid - read-only observation TUI (Phase 2). No execution or mutation.",
    )
    parser.add_argument("--base-url", default=ReadSurfaceClient.DEFAULT_BASE_URL,
                        help="ACT-MCE read surface base URL (default: %(default)s)")
    parser.add_argument("--fixture", default=None,
                        help="Path to sample fixture JSON for OFFLINE PREVIEW (marked data only)")
    sub = parser.add_subparsers(dest="cmd", help="read-only subcommands (default: full view)")

    sub.add_parser("show-health", help="Show only health status (read surface or fixture)")
    sub.add_parser("show-current", help="Show run_current snapshot (read-only)")
    sub.add_parser("show-stats", help="Show aggregate stats (read-only)")

    args = parser.parse_args(argv)

    client = ReadSurfaceClient(base_url=args.base_url)
    tui = ACTHybridViewerTUI(client=client)

    fixture = args.fixture
    snap: Dict[str, Any] = {}
    if fixture:
        snap = client.get_snapshot_from_fixture(fixture)
        tui._last_snapshot = snap
        tui._fixture_used = True
        tui._offline = True  # treat fixture as offline from live
    else:
        # for subcommands we may still want partial
        snap = tui.refresh()  # live attempt

    cmd = args.cmd or "full"

    if cmd == "show-health":
        h = snap.get("health", client.health() if not fixture else {})
        print("HEALTH (read-only):")
        print(json.dumps(h, indent=2, default=str) if isinstance(h, dict) else str(h))
    elif cmd == "show-current":
        rc = snap.get("run_current", {})
        print("RUN CURRENT (read-only snapshot):")
        print(json.dumps(rc, indent=2, default=str))
    elif cmd == "show-stats":
        st = snap.get("stats", {})
        print("STATS (read-only):")
        print(json.dumps(st, indent=2, default=str))
    else:
        # full refined TUI view
        tui.run(auto_refresh=False, fixture_path=fixture if fixture else None)

    # Always remind boundary on CLI use
    print("\n" + "─" * 60)
    print("OBSERVATION ONLY — no execute, approve, advance, or mutation performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
