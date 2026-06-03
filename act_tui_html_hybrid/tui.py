"""
Phase 2 TUI for ACT TUI/HTML Hybrid viewer (refined visual/readability; current scaffold).

**Current scaffold phase:** Displays improved layout of read/render-only sections from the read surface or sample fixtures.
TUI here supports OBSERVATION + LOCAL COMPOSE/PREVIEW of Engine Command Envelopes (for ACT-MCE).
Clear unavailable/offline states. Compose/preview is local only (no submission path, no execution).

**Future target role for TUI:** operator request/input surface (gated Engine command API only; not in this repo/phase).
Composition here prepares envelopes that *could* be submitted later via the gated seam.

The viewer observes (current) + composes envelopes locally. The engine decides. Gates decide advancement.
Operator acceptance remains final.

Forbidden in this module (permanent + current):
- No execute, approve, advance, run, mutate, or *submission* actions exposed.
- No direct execution/mutation/gate bypass/receipt writing/self-approve (ever).
- All display/refresh/compose are read-only or local-preview (current posture).
- Uses only the ReadSurfaceClient (GET only) or fixture loads (preview).
- No real command submission (current; future gated requests only via Engine API, never direct).
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional

from .read_surface_client import ReadSurfaceClient
from .command_envelope import (
    CommandEnvelope,
    CommandResult,
    CommandType,
    KNOWN_COMMAND_TYPES,
    preview_envelope,
)


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
        # Local compose/preview state (never submitted, never executed, never mutated)
        self._composed_envelopes: list[CommandEnvelope] = []
        self._last_preview: Optional[Dict[str, Any]] = None

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

        # COMMAND ENVELOPE COMPOSER (local TUI preview only — never submitted/executed here)
        if self._last_preview:
            env = self._last_preview.get("envelope", {})
            res = self._last_preview.get("preview_result", {})
            comp_lines = [
                f"command_id: {env.get('command_id', 'n/a')}",
                f"type: {env.get('command_type', 'n/a')}  target: {env.get('target') or '(none)'}",
                f"dry_run: {env.get('dry_run', False)}  requires_gate: {env.get('requires_gate', True)}",
                f"inputs: {json.dumps(env.get('inputs', {}))[:60]}...",
            ]
            lines.extend(self._box("COMMAND ENVELOPE (LOCAL COMPOSE/PREVIEW — TUI only)", comp_lines))
            prev_lines = [
                f"preview_status: {res.get('status', 'n/a')}",
                f"next_action: {res.get('next_action', '')[:65]}",
            ]
            if res.get("warnings"):
                prev_lines.append(f"warnings: {res['warnings'][0][:50]}...")
            lines.extend(self._box("PREVIEW RESULT (stub — no Engine execution)", prev_lines))
            lines.append(self._c("  (Use CLI 'compose-envelope' to create new previews. This surface does not submit.)", self.DIM))
        else:
            lines.extend(self._box("COMMAND ENVELOPE COMPOSER", [
                "(no envelope composed in this session yet)",
                "Use CLI: ... tui compose-envelope --type list_wrappers ...",
                "Local preview only. Engine decides on any future submit.",
            ]))
        lines.append("")

        # Footer controls / boundary (no actions)
        lines.append(self._c("─" * 78, self.DIM))
        lines.append(self._c("KEYS (read-only placeholder): [r]efresh  [q]uit   |  No execute / approve / advance exposed.", self.DIM))
        lines.append(self._c("This surface OBSERVES + COMPOSES (envelopes) only. Engine decides. Operator acceptance remains final.", self.BOLD))
        if self._fixture_used:
            lines.append(self._c("FIXTURE MODE: Sample data for preview. See _meta in data for provenance.", self.YELLOW))
        if self._composed_envelopes:
            lines.append(self._c(f"COMPOSED: {len(self._composed_envelopes)} local envelope(s) for preview (not sent).", self.CYAN))
        lines.append(self._c("─" * 78, self.DIM))
        return "\n".join(lines)

    # --- NEW: Local compose / preview for Engine Command Envelopes (TUI-side only) ---
    # These methods allow the TUI to *compose* and *preview* envelopes locally.
    # NEVER executes, NEVER mutates ACT-MCE, NEVER submits (no write client here).
    # Previews use the local model + stub result for operator awareness.
    # Future: these may be sent via gated Engine command API (outside this repo).

    def compose_envelope(
        self,
        command_type: str,
        target: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        requested_by: str = "operator",
        requires_gate: bool = True,
        dry_run: bool = False,
        command_id: Optional[str] = None,
    ) -> CommandEnvelope:
        """Compose (and store) a CommandEnvelope locally for preview."""
        env = CommandEnvelope.compose(
            command_type=command_type,
            target=target,
            inputs=inputs,
            requested_by=requested_by,
            requires_gate=requires_gate,
            dry_run=dry_run,
            command_id=command_id,
        )
        self._composed_envelopes.append(env)
        self._last_preview = preview_envelope(env)
        return env

    def get_last_envelope_preview(self) -> Optional[Dict[str, Any]]:
        """Return the most recent local compose preview (envelope + stub result)."""
        return self._last_preview

    def clear_composed(self) -> None:
        """Clear local composed state (purely for this TUI session preview)."""
        self._composed_envelopes.clear()
        self._last_preview = None

    def run(self, auto_refresh: bool = True, fixture_path: str | None = None) -> None:
        """Run a single-pass refined render (read-only)."""
        if auto_refresh:
            self.refresh(fixture_path=fixture_path)
        print(self.render())
        print(self._c("\n(Observation + compose/preview surface only. Single-pass placeholder. No controls for execution/approval/advancement/submission.)", self.DIM))

    # Explicitly no mutation surfaces
    # Intentionally omitted: execute, approve, advance, request_run, mutate, etc.


def main(argv: list[str] | None = None) -> int:
    """CLI entry for python -m act_tui_html_hybrid.tui

    Supports:
      (default)          full refined TUI render of current or fixture (includes local envelope composer section if used)
      show-health        print health only
      show-current       print run_current snapshot
      show-stats         print stats
      compose-envelope   COMPOSE + PREVIEW a local Engine Command Envelope (for ACT-MCE).
                         --type (required, from known list), --target, --inputs (json or k=v), --dry-run, --no-gate, --id
                         Produces pretty JSON of envelope + stub preview result.
                         LOCAL ONLY. Validates. NEVER executes, NEVER mutates, NEVER submits (no write path here).
    All use --base-url or --fixture for offline preview (state observation).
    Never executes, never mutates, never submits.
    """
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="act_tui_html_hybrid.tui",
        description="ACT TUI/HTML Hybrid - read-only observation + local envelope compose/preview TUI. No execution, no mutation, no submission.",
    )
    parser.add_argument("--base-url", default=ReadSurfaceClient.DEFAULT_BASE_URL,
                        help="ACT-MCE read surface base URL (default: %(default)s)")
    parser.add_argument("--fixture", default=None,
                        help="Path to sample fixture JSON for OFFLINE PREVIEW (marked data only)")
    sub = parser.add_subparsers(dest="cmd", help="read-only subcommands (default: full view)")

    sub.add_parser("show-health", help="Show only health status (read surface or fixture)")
    sub.add_parser("show-current", help="Show run_current snapshot (read-only)")
    sub.add_parser("show-stats", help="Show aggregate stats (read-only)")

    # Compose/preview subcommand (local TUI only; produces no side effects, no network writes)
    compose_p = sub.add_parser(
        "compose-envelope",
        help="Compose and preview a local Engine Command Envelope (for ACT-MCE). Validation + pretty JSON preview + stub result. NEVER executes or submits.",
    )
    compose_p.add_argument("--type", required=True, choices=sorted(KNOWN_COMMAND_TYPES),
                           help="Command type (must be known to ACT-MCE Engine)")
    compose_p.add_argument("--target", default=None, help="Optional target for the command (e.g. agent id, path, schema)")
    compose_p.add_argument("--inputs", default="{}", help="JSON string for inputs dict, or key=val,key2=val2")
    compose_p.add_argument("--dry-run", action="store_true", help="Mark as dry_run (preview only)")
    compose_p.add_argument("--no-gate", action="store_true", help="Set requires_gate=false (Engine would still decide)")
    compose_p.add_argument("--id", default=None, help="Optional explicit command_id (auto-generated if omitted)")

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
    elif cmd == "compose-envelope":
        # Local compose + preview ONLY. Parse inputs flexibly.
        try:
            if args.inputs.strip().startswith("{"):
                inputs = json.loads(args.inputs)
            else:
                # simple key=val,key2=val2 parser
                inputs = {}
                for pair in args.inputs.split(","):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        inputs[k.strip()] = v.strip()
            env = tui.compose_envelope(
                command_type=args.type,
                target=args.target,
                inputs=inputs,
                dry_run=args.dry_run,
                requires_gate=not args.no_gate,
                command_id=args.id,
            )
            preview = tui.get_last_envelope_preview() or {}
            print("=== LOCAL ENGINE COMMAND ENVELOPE (COMPOSED/PREVIEW — TUI only) ===")
            print("ENVELOPE:")
            print(env.to_json())
            print("\nPREVIEW RESULT (stub, local only; no Engine call, no execution, no mutation):")
            print(json.dumps(preview.get("preview_result", {}), indent=2, default=str))
            print("\n" + "─" * 60)
            print("BOUNDARY: This is LOCAL COMPOSE + PREVIEW only. Never executed. Never submitted.")
            print("Engine Command Manager (ACT-MCE) will validate/gate/decide on any future gated submit.")
        except Exception as e:
            print(f"COMPOSE ERROR: {e}")
            print("Valid types:", sorted(KNOWN_COMMAND_TYPES))
            return 1
    else:
        # full refined TUI view
        tui.run(auto_refresh=False, fixture_path=fixture if fixture else None)

    # Always remind boundary on CLI use
    print("\n" + "─" * 60)
    print("OBSERVATION + COMPOSE/PREVIEW ONLY — no execute, approve, advance, submission, or mutation performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
