"""
Local Command Envelope model for ACT TUI/HTML Hybrid (mirrored from ACT-MCE Engine contract).

This allows the TUI to COMPOSE and PREVIEW Engine Command Envelopes locally
for operator review before any (future) gated submission.

IMPORTANT BOUNDARIES (enforced here and in tests):
- Pure data + local validation/preview ONLY.
- NO execution of any kind.
- NO mutation of ACT-MCE state, repo, or anything.
- NO network/POST/submission (this repo's read client is GET-only; no write client here).
- NO imports of ACT-MCE engine, gates, capabilities, registry, runtime, etc.
- HTML surface remains view-only (stats/graphs/readouts/exports + static envelope previews).
- TUI compose/preview is for awareness and preparation; Engine decides everything.

Mirrors the contract shapes from ACT-MCE for compatibility:
  - CommandEnvelope (with validation for known types + required id)
  - CommandResult (stub previews only, never real results)

See docs/BOUNDARY.md for full separation.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from enum import Enum
import datetime
import json


class CommandType(str, Enum):
    """Known command types (mirrored from ACT-MCE for TUI composition)."""
    SPAWN_AGENT = "spawn_agent"
    RUN_GATE = "run_gate"
    RUN_HOOK = "run_hook"
    INSPECT_SCHEMA = "inspect_schema"
    INSPECT_PATH = "inspect_path"
    LIST_WRAPPERS = "list_wrappers"
    LIST_HOOKS = "list_hooks"
    LIST_OUTPUTS = "list_outputs"
    LIST_INPUTS = "list_inputs"


KNOWN_COMMAND_TYPES: set[str] = {ct.value for ct in CommandType}


@dataclass
class CommandEnvelope:
    """Envelope for composing operator commands to Engine (TUI-side preview only).

    The TUI builds these locally. Validation happens here for immediate feedback.
    Submission (future, via gated Engine API) is outside this repo's scope.
    """
    command_id: str
    command_type: str
    target: Optional[str] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    requested_by: str = "operator"
    requires_gate: bool = True
    dry_run: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )

    def __post_init__(self) -> None:
        if not self.command_id or not isinstance(self.command_id, str) or not self.command_id.strip():
            raise ValueError("command_id is required and must be a non-empty string")
        if self.command_type not in KNOWN_COMMAND_TYPES:
            raise ValueError(
                f"Unknown command_type '{self.command_type}'. "
                f"Known types for preview: {sorted(KNOWN_COMMAND_TYPES)}"
            )
        if not isinstance(self.inputs, dict):
            raise ValueError("inputs must be a dict")
        if not isinstance(self.dry_run, bool):
            raise ValueError("dry_run must be boolean")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), default=str, indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandEnvelope":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def compose(
        cls,
        command_type: str,
        target: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        requested_by: str = "operator",
        requires_gate: bool = True,
        dry_run: bool = False,
        command_id: Optional[str] = None,
    ) -> "CommandEnvelope":
        """Convenience composer for TUI/CLI use. Auto-generates command_id if not provided."""
        if command_id is None:
            import uuid
            command_id = f"cmd_{uuid.uuid4().hex[:8]}"
        return cls(
            command_id=command_id,
            command_type=command_type,
            target=target,
            inputs=inputs or {},
            requested_by=requested_by,
            requires_gate=requires_gate,
            dry_run=dry_run,
        )


@dataclass
class CommandResult:
    """Stub/preview result for a composed envelope (TUI-side only, never real Engine output).

    Used for local preview of what a submission *might* produce.
    Does not represent actual execution, gating, or receipts.
    """
    command_id: str
    status: str = "preview"  # preview | accepted | rejected | etc. (local only)
    gate_status: Optional[str] = None
    receipt_path: Optional[str] = None
    output_paths: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    next_action: Optional[str] = "This is a LOCAL PREVIEW only. No submission or execution occurred."
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Loose validation for preview; real status rules are in Engine.
        pass

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), default=str, indent=indent, sort_keys=True)


def preview_envelope(envelope: CommandEnvelope) -> Dict[str, Any]:
    """Generate a local preview dict: the envelope + a stub result.

    Never executes, never contacts Engine, purely for TUI operator preview.
    """
    # Simple heuristic preview (local only, not real)
    warnings = []
    if envelope.dry_run:
        warnings.append("dry_run=True: would request no side effects from Engine")
    if envelope.requires_gate:
        warnings.append("requires_gate=True: Engine would evaluate before acting (future)")
    if not envelope.target and envelope.command_type not in ("list_wrappers", "list_hooks", "list_inputs", "list_outputs"):
        warnings.append("No target specified; some commands may require one")

    stub_result = CommandResult(
        command_id=envelope.command_id,
        status="preview",
        gate_status=None,
        warnings=warnings + ["LOCAL COMPOSE/PREVIEW — not submitted, not executed, not approved"],
        metadata={
            "composed_by": envelope.requested_by,
            "command_type": envelope.command_type,
            "preview_note": "This TUI surface only composes and previews. Engine Command Manager decides and executes (if ever submitted via gated API).",
        },
    )

    return {
        "envelope": envelope.to_dict(),
        "preview_result": stub_result.to_dict(),
        "boundary": "TUI observes + composes. Engine decides + executes. No mutation here.",
    }
