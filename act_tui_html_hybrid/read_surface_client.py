"""
Read Surface Client for ACT TUI/HTML Hybrid.

Strictly consumes the ACT-MCE localhost read surface via GET only.
This is an observation client. It never mutates state, never executes,
never approves, never advances phases.

The viewer observes. The engine decides. Gates decide advancement.
Operator acceptance remains final.
"""

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict


class ReadSurfaceClient:
    """Minimal read-only client for the ACT-MCE read surface.

    All operations are GET. Connection failures are handled gracefully
    by returning an error dict instead of raising or crashing the caller.
    """

    DEFAULT_BASE_URL = "http://127.0.0.1:8765"

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")

    def _get(self, path: str) -> Dict[str, Any]:
        """Perform a single GET. Returns parsed JSON or graceful error dict."""
        if not path.startswith("/"):
            path = "/" + path
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            # Server responded with error (e.g. 404, 405)
            try:
                body = e.read().decode("utf-8")
                data = json.loads(body)
                data.setdefault("source", "read_surface_client")
                return data
            except Exception:
                return {
                    "error": f"HTTP {e.code}",
                    "source": "read_surface_client",
                    "path": path,
                    "available": False,
                }
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            return {
                "error": f"Read surface unavailable: {e}",
                "source": "read_surface_client",
                "path": path,
                "available": False,
            }
        except json.JSONDecodeError as e:
            return {
                "error": f"Invalid JSON from read surface: {e}",
                "source": "read_surface_client",
                "path": path,
            }
        except Exception as e:
            return {
                "error": f"Unexpected client error: {e}",
                "source": "read_surface_client",
                "path": path,
            }

    def health(self) -> Dict[str, Any]:
        """GET /health - server liveness/read-only declaration."""
        return self._get("/health")

    def run_current(self) -> Dict[str, Any]:
        """GET /run/current - current run snapshot (Stage 1 admission view)."""
        return self._get("/run/current")

    def run_stats(self) -> Dict[str, Any]:
        """GET /run/stats - aggregate counts for the run."""
        return self._get("/run/stats")

    def events(self) -> Dict[str, Any]:
        """GET /events - read-only event records."""
        return self._get("/events")

    def receipts(self) -> Dict[str, Any]:
        """GET /receipts - receipt summaries (engine-owned only)."""
        return self._get("/receipts")

    def gates(self) -> Dict[str, Any]:
        """GET /gates - gate summaries (engine-owned only)."""
        return self._get("/gates")

    def traces(self) -> Dict[str, Any]:
        """GET /traces - trace summaries."""
        return self._get("/traces")

    def warnings(self) -> Dict[str, Any]:
        """GET /warnings - current warnings for operator awareness."""
        return self._get("/warnings")

    def fetch_snapshot(self) -> Dict[str, Any]:
        """Convenience: fetch a minimal combined view using only read methods."""
        return {
            "health": self.health(),
            "run_current": self.run_current(),
            "stats": self.run_stats(),
            "receipts": self.receipts(),
            "gates": self.gates(),
            "warnings": self.warnings(),
        }

    def load_fixture(self, fixture_path: str) -> Dict[str, Any]:
        """Load sample fixture JSON for offline preview / layout testing.

        The fixture MUST be clearly marked as SAMPLE/PREVIEW only.
        This does not perform any GETs and is strictly for read-only preview.
        Returns the loaded data (caller decides how to render sections).
        """
        p = Path(fixture_path)
        if not p.is_file():
            return {
                "error": f"Fixture not found: {fixture_path}",
                "source": "read_surface_client",
                "available": False,
                "_meta": {"source": "FIXTURE_LOAD_ERROR"}
            }
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            # Ensure preview marker is present for safety
            meta = data.get("_meta", {})
            if "SAMPLE_FIXTURE_PREVIEW_ONLY" not in str(meta):
                data.setdefault("_meta", {})["note"] = (
                    data.get("_meta", {}).get("note", "") +
                    " [WARNING: not explicitly marked as SAMPLE_FIXTURE_PREVIEW_ONLY]"
                )
            data["_meta"] = data.get("_meta", {})
            data["_meta"]["loaded_from"] = str(p)
            self._last_fixture = data
            return data
        except Exception as e:
            return {
                "error": f"Failed to load fixture {fixture_path}: {e}",
                "source": "read_surface_client",
                "path": str(p),
            }

    def get_snapshot_from_fixture(self, fixture_path: str) -> Dict[str, Any]:
        """Load fixture and return a snapshot-shaped dict using its top-level sections.

        Falls back to combining known keys if fixture is a full snapshot.
        """
        data = self.load_fixture(fixture_path)
        if "error" in data:
            return data
        # If fixture already looks like a combined snapshot from fetch_snapshot, use as-is
        if all(k in data for k in ("health", "run_current", "stats", "receipts", "gates", "warnings")):
            return data
        # Otherwise wrap minimal
        return {
            "health": data.get("health", {"status": "FIXTURE", "read_only": True}),
            "run_current": data.get("run_current", {}),
            "stats": data.get("stats", {}),
            "receipts": data.get("receipts", {}),
            "gates": data.get("gates", {}),
            "warnings": data.get("warnings", {}),
            "_meta": data.get("_meta", {"source": "SAMPLE_FIXTURE_PREVIEW_ONLY"}),
        }
