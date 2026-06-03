"""
Tests for the initial ACT TUI/HTML Hybrid viewer scaffold.

These tests enforce the observation-only contract:
- Client uses GET exclusively.
- No forbidden ACT-MCE engine imports.
- No mutation actions or verbs implemented.
- TUI and HTML are strictly read surfaces.
- README declares observation surface only.
"""

import ast
import inspect
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure we can import the package under test without installation
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from act_tui_html_hybrid import (
    ReadSurfaceClient,
    ACTHybridViewerTUI,
    render_read_only_html,
    export_html_to_file,
)
from act_tui_html_hybrid.read_surface_client import ReadSurfaceClient as RSC
from act_tui_html_hybrid.tui import ACTHybridViewerTUI as TUI
from act_tui_html_hybrid.html_export import render_read_only_html as render_html


FORBIDDEN_IMPORT_SUBSTRINGS = [
    "act_mce",
    "act_mce.gates",
    "act_mce.capabilities",
    "act_mce.core",
    "act_mce.runtime",
    "gate",
    "capability",
    "registry",
    "execution",
    "runner",
    "mutation",
]

MUTATION_VERBS = [
    "post",
    "put",
    "patch",
    "delete",
    "execute",
    "approve",
    "advance",
    "mutate",
    "write_receipt",
    "run_card",
    "phase_advance",
]

TUI_FORBIDDEN_ACTIONS = [
    "execute",
    "approve",
    "advance",
    "run_card",
    "request_approval",
    "perform_action",
    "mutate_state",
]


def _get_module_source(mod) -> str:
    try:
        return inspect.getsource(mod)
    except Exception:
        # fallback to file
        f = inspect.getfile(mod)
        return Path(f).read_text(encoding="utf-8")


def _collect_import_strings(tree: ast.AST) -> list[str]:
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def test_package_imports_cleanly():
    """Basic smoke: the public API is importable."""
    assert ReadSurfaceClient is not None
    assert ACTHybridViewerTUI is not None
    assert callable(render_read_only_html)


def test_client_only_uses_get_runtime():
    """Client constructs only GET requests (runtime proof via patched urlopen)."""
    client = ReadSurfaceClient(base_url="http://127.0.0.1:1")  # invalid port to avoid real net

    captured = []

    def fake_urlopen(req, **kwargs):
        captured.append(req)
        # simulate connection failure so we don't hang
        raise Exception("forced test failure for capture")

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        client.health()
        client.run_current()
        client.gates()

    assert len(captured) >= 3
    for req in captured:
        # urllib.request.Request stores the method
        method = getattr(req, "method", None) or getattr(req, "_method", "GET")
        assert method == "GET", f"Non-GET method used: {method} on {getattr(req, 'full_url', req)}"


def test_client_only_uses_get_static_source():
    """Source inspection: client module contains the literal 'GET' and no mutation verbs."""
    src = _get_module_source(RSC)
    tree = ast.parse(src)

    # Must mention GET for the requests we build
    assert "GET" in src or "method=\"GET\"" in src or "method='GET'" in src

    lowered = src.lower()
    for verb in ["post(", "put(", "patch(", "delete(", ".post", ".put", ".patch", ".delete"]:
        assert verb not in lowered, f"Forbidden HTTP verb found in client source: {verb}"

    # Also no obvious mutation symbols in the implemented surface
    for bad in ["execute", "approve", "advance", "write_receipt"]:
        assert bad not in lowered, f"Forbidden action symbol in client: {bad}"


def test_client_handles_server_unavailable_gracefully():
    """When the read server is down, every method returns a graceful error dict (no crash)."""
    client = ReadSurfaceClient(base_url="http://127.0.0.1:1")  # nothing listening

    for method_name in ["health", "run_current", "run_stats", "events", "receipts", "gates", "traces", "warnings"]:
        meth = getattr(client, method_name)
        result = meth()
        assert isinstance(result, dict)
        # Either has explicit error or available:false marker
        has_error = "error" in result or result.get("available") is False
        assert has_error, f"{method_name} did not handle unavailability gracefully: {result}"
        # Should still be usable by TUI/HTML without blowing up
        assert "source" in result or "path" in result


def test_no_forbidden_imports_in_source():
    """Static analysis: none of the package modules import forbidden engine modules."""
    package_dir = ROOT / "act_tui_html_hybrid"
    py_files = list(package_dir.glob("*.py"))

    assert py_files, "No python files found in package"

    for py in py_files:
        src = py.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(py))
        imports = _collect_import_strings(tree)

        for imp in imports:
            lowered = imp.lower()
            for forbidden in FORBIDDEN_IMPORT_SUBSTRINGS:
                assert forbidden not in lowered, (
                    f"Forbidden import '{imp}' found in {py.name} (matched {forbidden})"
                )

        # Also direct string checks for safety (e.g. dynamic or comments that would still be bad)
        lowered_src = src.lower()
        for forbidden in ["from act_mce", "import act_mce", "act_mce.gates", "act_mce.capabilities"]:
            assert forbidden not in lowered_src, f"Forbidden import string in {py.name}: {forbidden}"


def test_no_mutation_verbs_as_implemented_routes_or_actions():
    """Source must not contain implemented POST routes or mutation action methods."""
    for mod in [RSC, TUI, render_html]:
        src = _get_module_source(mod).lower()
        for verb in MUTATION_VERBS:
            # Look for common patterns that would indicate an implemented action
            patterns = [f"def {verb}", f".{verb}(", f'"{verb}"', f"'{verb}'", f"/{verb}"]
            for p in patterns:
                assert p not in src, f"Mutation verb/action '{verb}' appears in {mod.__name__} source via {p}"

    # Extra: the client must never define anything but the declared GET methods
    client_src = _get_module_source(RSC)
    # Only the 8 + helpers allowed
    allowed = {"health", "run_current", "run_stats", "events", "receipts", "gates", "traces", "warnings", "_get", "fetch_snapshot", "__init__"}
    tree = ast.parse(client_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if not node.name.startswith("_") or node.name in {"_get"}:
                assert node.name in allowed or node.name.startswith("test_"), (
                    f"Unexpected method {node.name} on client (risk of hidden action)"
                )


def test_tui_does_not_expose_execute_approve_advance_actions():
    """TUI class and instances must not expose execute/approve/advance surfaces."""
    tui = ACTHybridViewerTUI()

    for name in TUI_FORBIDDEN_ACTIONS:
        assert not hasattr(tui, name), f"TUI instance exposes forbidden action: {name}"
        assert not hasattr(ACTHybridViewerTUI, name), f"TUI class exposes forbidden action: {name}"

    # Render must succeed and mention read-only posture
    tui.refresh()  # will be disconnected but must not crash
    rendered = tui.render()
    assert "read-only" in rendered.lower() or "observes only" in rendered.lower()
    assert "No execute" in rendered or "No execute / approve / advance" in rendered

    # Source level: no def of the bad actions
    tui_src = _get_module_source(TUI).lower()
    for bad in TUI_FORBIDDEN_ACTIONS:
        assert f"def {bad}" not in tui_src, f"TUI source defines forbidden def {bad}"


def test_html_export_is_read_only():
    """HTML export produces static read-only markup with no mutation affordances."""
    # Provide a fake snapshot so no network
    fake = {
        "health": {"status": "OK", "read_only": True},
        "run_current": {"run_id": "RUN_TEST", "status": "UNKNOWN", "admission_stage": "STAGE_1"},
        "stats": {"counts": {"receipts": 0, "gates": 1, "warnings": 1}},
        "receipts": {"receipts": []},
        "gates": {"gates": [{"gate_id": "stage_1_admission_gate", "status": "UNKNOWN"}]},
        "warnings": {"warnings": [{"message": "test warning"}]},
    }

    html = render_read_only_html(fake)
    assert "<!DOCTYPE html>" in html
    assert "read-only" in html.lower()
    assert "Read-Only Snapshot" in html

    # Must contain no <form method= (case insensitive) that could post
    html_lower = html.lower()
    assert "<form" not in html_lower, "HTML export contains a form (forbidden for read-only)"
    for bad in ["method=\"post\"", "method='post'", "method=post", "onclick=", "onchange=", ".post("]:
        assert bad not in html_lower, f"HTML contains potential mutation hook: {bad}"

    # Can export to file
    out = ROOT / "tests" / "_tmp_readonly_export.html"
    out.parent.mkdir(exist_ok=True)
    p = export_html_to_file(str(out), fake)
    assert Path(p).exists()
    content = Path(p).read_text(encoding="utf-8")
    assert "ACT TUI/HTML Hybrid" in content
    # cleanup not strictly needed for test run
    # Path(p).unlink(missing_ok=True)


def test_readme_states_observation_surface_only():
    """README must explicitly declare this is an observation surface only."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "observation surface only" in readme
    assert "the viewer observes" in readme
    assert "engine decides" in readme
    # Also calls out the key prohibitions
    assert "no post" in readme or "strictly get-only" in readme
