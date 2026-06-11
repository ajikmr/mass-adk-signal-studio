"""Read-only tools for integrated `mass_engine` run artifacts."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mass_engine.cloud import create_artifact_store
from mass_engine.runner import DEFAULT_LOCAL_ARTIFACT_ROOT


def _backend() -> str:
    return os.getenv("MASS_ADK_ARTIFACT_BACKEND", "local").lower()


def _store():
    return create_artifact_store(
        backend=_backend(),
        local_root=os.getenv("MASS_ADK_LOCAL_ARTIFACT_ROOT", str(DEFAULT_LOCAL_ARTIFACT_ROOT)),
        bucket=os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET"),
        prefix=os.getenv("MASS_ADK_GCS_PREFIX", "mass-adk"),
    )


def _safe_run_id(run_id: str) -> str | None:
    cleaned = run_id.strip()
    if not cleaned or "/" in cleaned or "\\" in cleaned or ".." in cleaned:
        return None
    return cleaned


def list_mass_engine_runs(limit: int = 20) -> dict[str, Any]:
    """List integrated MASS engine run manifests from the configured artifact store.

    Args:
        limit: Maximum number of run records to return.
    """

    store = _store()
    artifact_paths = store.list("runs")
    run_ids = sorted({Path(path).parts[1] for path in artifact_paths if path.startswith("runs/")})
    records = []
    for run_id in run_ids[: max(1, min(limit, 200))]:
        record: dict[str, Any] = {"run_id": run_id}
        manifest_path = f"runs/{run_id}/manifest.json"
        progress_path = f"runs/{run_id}/progress.json"
        if store.exists(manifest_path):
            manifest = store.read_json(manifest_path)
            record.update(
                {
                    "mode": manifest.get("mode"),
                    "artifact_backend": manifest.get("artifact_backend"),
                    "adk_model": manifest.get("adk_model") or manifest.get("model"),
                    "engine_model": manifest.get("engine_model"),
                    "stock_pool": manifest.get("parameters", {}).get("stock_pool"),
                    "created_at": manifest.get("created_at"),
                }
            )
        if store.exists(progress_path):
            progress = store.read_json(progress_path)
            record.update(
                {
                    "status": progress.get("status"),
                    "executed": progress.get("executed"),
                    "completed_at": progress.get("completed_at"),
                }
            )
        records.append(record)

    return {
        "artifact_backend": _backend(),
        "runs": records,
        "count": len(records),
        "note": "These are integrated MASS engine run records written by mass_engine.runner, not original before-version MASS artifacts.",
    }


def inspect_mass_engine_run(run_id: str) -> dict[str, Any]:
    """Inspect one integrated MASS engine run manifest and progress record.

    Args:
        run_id: Direct run id from `list_mass_engine_runs`.
    """

    safe_run_id = _safe_run_id(run_id)
    if safe_run_id is None:
        return {"error": "Invalid run_id. Use a direct run id only.", "run_id": run_id}

    store = _store()
    manifest_path = f"runs/{safe_run_id}/manifest.json"
    progress_path = f"runs/{safe_run_id}/progress.json"
    if not store.exists(manifest_path) and not store.exists(progress_path):
        return {
            "error": "Integrated MASS engine run not found.",
            "run_id": safe_run_id,
            "artifact_backend": _backend(),
        }

    return {
        "run_id": safe_run_id,
        "artifact_backend": _backend(),
        "manifest": store.read_json(manifest_path) if store.exists(manifest_path) else None,
        "progress": store.read_json(progress_path) if store.exists(progress_path) else None,
        "interpretation": "This is an after-version MASS-ADK run record. Dry-run records prove packaging and artifact-store routing without launching expensive simulations.",
    }
