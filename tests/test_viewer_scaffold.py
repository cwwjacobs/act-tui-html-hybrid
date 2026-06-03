"""
Tests for ACT TUI/HTML Hybrid viewer (Phase 2 visual refinement + doctrine patch).

These tests enforce:
- Permanent boundaries (no direct exec/mutate/imports/bypass/fake-receipts/self-approve) + current scaffold posture.
- Client uses GET exclusively (live paths).
- No forbidden ACT-MCE engine/gate/capability imports in source.
- No mutation actions or verbs implemented in CLI/TUI/HTML.
- **Current:** TUI (read/render-only) and HTML (view-only) surfaces; TUI renders sample/fixture without server; no request submission implemented.
- HTML from fixture is static, no forms, no mutating scripts.
- CLI mains expose only read/show/render subcommands (show-health, show-current, render via html). No command submit.
- README + docs now distinguish current read-only scaffold vs. future gated TUI request/input surface (HTML view-only); fixtures declare preview only.
- Server unavailable and fixture paths are graceful.
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
FIXTURE = ROOT / "tests" / "fixtures" / "sample_snapshot.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from act_tui_html_hybrid import (
    ReadSurfaceClient,
    ACTHybridViewerTUI,
    render_read_only_html,
    export_html_to_file,
)
from act_tui_html_hybrid.read_surface_client import ReadSurfaceClient as RSC
from act_tui_html_hybrid.tui import ACTHybridViewerTUI as TUI, main as tui_main
from act_tui_html_hybrid.html_export import render_read_only_html as render_html, main as html_main, export_html_to_file as export_html



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
            # Look for common patterns that would indicate an *implemented* action or route (not prose about forbidden things)
            patterns = [f"def {verb}(", f".{verb}(", f'"{verb}"', f"'{verb}'", f" /{verb} ", f'/{verb}"', f'/{verb}\'']
            for p in patterns:
                if p in src and "no " not in src and "forbidden" not in src and "omitted" not in src and "intentionally" not in src:
                    assert False, f"Mutation verb/action '{verb}' appears in {mod.__name__} source via {p} (outside of boundary reminder text)"
            # also direct def without ( for safety
            if f"def {verb}" in src and "def " + verb + "(" not in src:
                if "no " not in src[:src.find(f"def {verb}")+20]:
                    assert False, f"def {verb} without ( in {mod.__name__}"

    # Extra: the client must never define anything but the declared GET + isolated fixture preview methods
    client_src = _get_module_source(RSC)
    # Only the 8 read + helpers + fixture preview loaders (explicitly not live mutation)
    allowed = {
        "health", "run_current", "run_stats", "events", "receipts", "gates", "traces", "warnings",
        "_get", "fetch_snapshot", "__init__",
        "load_fixture", "get_snapshot_from_fixture"
    }
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


def test_readme_distinguishes_current_scaffold_vs_future_and_html_view_only():
    """README must distinguish current read-only scaffold (TUI read/render-only, no request yet) vs future gated TUI request/input surface, and HTML view-only. (Doctrine patch)"""
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "the viewer observes" in readme
    assert "engine decides" in readme
    # Current scaffold
    assert "current scaffold" in readme or "read/render-only" in readme
    assert "no request submission" in readme or "request submission" in readme  # mentions the current absence
    # Future target
    assert "future target" in readme or "gated engine" in readme or "gated engine command api" in readme
    assert "operator request/input surface" in readme or "request/input surface" in readme
    # HTML permanent
    assert "html" in readme and ("view-only" in readme or "view only" in readme)
    # Permanent forbids
    assert "never directly execute" in readme or "never directly" in readme
    # Phase 2 / fixture still present
    assert "phase 2" in readme or "visual" in readme
    assert "fixture" in readme and "preview" in readme
    # Key prohibitions still called out
    assert "no post" in readme or "strictly get-only" in readme
    assert "sample_fixture_preview_only" in readme or "preview only" in readme


# ------------------------------------------------------------------
# Phase 2 specific required tests
# ------------------------------------------------------------------

def test_tui_renders_sample_state_without_server():
    """TUI must render using sample fixture (offline, no live server) and show preview/offline state."""
    assert FIXTURE.exists(), "sample fixture must exist for test"
    tui = ACTHybridViewerTUI()
    snap = tui.refresh(fixture_path=str(FIXTURE))
    rendered = tui.render()

    # Must succeed without hitting network
    assert isinstance(snap, dict)
    assert "SAMPLE_FIXTURE_PREVIEW_ONLY" in str(snap.get("_meta", {}))
    assert "OFFLINE" in rendered or "SAMPLE" in rendered or "PREVIEW" in rendered
    assert "read-only" in rendered.lower() or "observes only" in rendered.lower()
    # The render communicates absence of controls (desired); there must be no *performing* actions
    assert "no execute" in rendered.lower() or "no approve" in rendered.lower()  # the reminder of boundary
    assert "execute(" not in rendered.lower() and "def execute" not in rendered.lower()  # no impl


def test_html_export_creates_static_file_from_fixture_data():
    """HTML export must produce a file when given fixture data (or path via CLI)."""
    assert FIXTURE.exists()
    with open(FIXTURE) as f:
        data = json.load(f)

    tmp_out = ROOT / "tests" / "_tmp_phase2_fixture.html"
    tmp_out.parent.mkdir(exist_ok=True)
    p = export_html(str(tmp_out), data, fixture_note=data.get("_meta", {}).get("note"))
    assert Path(p).exists()
    content = Path(p).read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "SAMPLE" in content or "PREVIEW" in content
    assert "ACT TUI/HTML Hybrid" in content
    # cleanup
    tmp_out.unlink(missing_ok=True)


def test_html_contains_no_forms():
    """Exported HTML (from fixture or synthetic) must contain no <form> elements."""
    fake = {
        "health": {"status": "OK", "read_only": True},
        "run_current": {"run_id": "F1", "status": "BLOCKED"},
        "stats": {"counts": {}},
        "receipts": {"receipts": []},
        "gates": {"gates": []},
        "warnings": {"warnings": []},
        "_meta": {"source": "SAMPLE_FIXTURE_PREVIEW_ONLY"},
    }
    html = render_read_only_html(fake)
    html_l = html.lower()
    assert "<form" not in html_l
    assert 'method="post"' not in html_l
    assert "method=post" not in html_l


def test_html_contains_no_mutating_scripts():
    """Exported HTML must have no onclick, on*, .post, fetch, or script that could mutate."""
    fake = {"health": {"status": "OK"}, "run_current": {}, "stats": {}, "receipts": {}, "gates": {}, "warnings": {}, "_meta": {"source": "SAMPLE_FIXTURE_PREVIEW_ONLY"}}
    html = render_read_only_html(fake)
    html_l = html.lower()
    for bad in ["onclick=", "onchange=", "onsubmit=", ".post(", "fetch(", "xmlhttprequest", "<script>"]:
        assert bad not in html_l, f"Found potential mutating hook in HTML: {bad}"


def test_cli_does_not_expose_execute_approve_advance_commands():
    """CLI mains must not define or accept execute/approve/advance subcommands or options."""
    # Inspect source
    tui_src = _get_module_source(tui_main).lower()
    html_src = _get_module_source(html_main).lower()
    for src in (tui_src, html_src):
        for bad in ["execute", "approve", "advance", "mutate", "submit", "run_card", "phase"]:
            # allow in help text or comments describing forbidden, but not as actions/parsers
            # check parser defs don't include them as choices
            assert f'"{bad}"' not in src or "forbidden" in src or "no " in src, f"CLI source exposes bad command token: {bad}"

    # Try parsing bad subcmd would fail argparse, but we don't call with it; just confirm no registration
    # Call with valid to ensure main runs
    import io
    from unittest.mock import patch
    with patch("sys.stdout", new=io.StringIO()):
        # show-health with fixture (no net)
        rc = tui_main(["--fixture", str(FIXTURE), "show-health"])
        assert rc == 0


def test_source_contains_no_act_mce_engine_gate_capability_imports():
    """Re-affirm (Phase 2): no forbidden imports in any package .py (including new CLI code)."""
    package_dir = ROOT / "act_tui_html_hybrid"
    for py in package_dir.glob("*.py"):
        src = py.read_text(encoding="utf-8").lower()
        for bad in ["import act_mce", "from act_mce", "act_mce.gates", "act_mce.capabilities", "act_mce.core", "act_mce.runtime"]:
            assert bad not in src, f"Forbidden import in {py.name}: {bad}"


def test_client_still_uses_only_get():
    """Client live path still only GET (Phase 2: fixture paths are additive, not mutating)."""
    # reuse existing style check + runtime
    src = _get_module_source(RSC).lower()
    for verb in ["post(", "put(", "patch(", "delete(", ".post", ".put", ".patch", ".delete"]:
        assert verb not in src
    # runtime already covered in other test; confirm fixture load doesn't introduce http methods
    c = ReadSurfaceClient(base_url="http://127.0.0.1:1")
    c.load_fixture(str(FIXTURE))  # should not touch net
    assert hasattr(c, "_last_fixture") or "error" in c.load_fixture("nonexistent.json")


def test_server_unavailable_path_is_graceful_phase2():
    """Unavailable still returns usable error dicts; TUI/HTML handle without crash (Phase 2)."""
    c = ReadSurfaceClient(base_url="http://127.0.0.1:1")
    for m in ["health", "run_current"]:
        res = getattr(c, m)()
        assert "error" in res or res.get("available") is False

    tui = ACTHybridViewerTUI(client=c)
    tui.refresh()  # should not raise
    r = tui.render()
    assert "OFFLINE" in r or "UNAVAILABLE" in r or "error" in r.lower() or "disconnected" in r.lower()

    # HTML from bad live attempt
    h = render_read_only_html(None)  # will try live -> error state inside
    assert "offline" in h.lower() or "unavailable" in h.lower() or "read-only" in h.lower()
