"""Dataset inspection tools."""

from __future__ import annotations

from typing import Any

from .manifest import load_manifest


def list_available_datasets() -> dict[str, Any]:
    """List datasets represented in the MASS-ADK cached evidence manifest."""

    manifest = load_manifest()
    return {
        "datasets": manifest["datasets"],
        "count": len(manifest["datasets"]),
        "note": "These are research datasets/signals, not live trading feeds.",
    }
