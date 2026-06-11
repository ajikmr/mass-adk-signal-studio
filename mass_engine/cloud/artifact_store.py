"""Artifact-store interface and factory for MASS engine runs."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ArtifactStore(ABC):
    """Minimal read/write interface for run artifacts."""

    @abstractmethod
    def write_json(self, path: str, payload: dict[str, Any]) -> str:
        """Write JSON and return the artifact URI/path."""

    @abstractmethod
    def read_json(self, path: str) -> dict[str, Any]:
        """Read JSON from an artifact path."""

    @abstractmethod
    def write_bytes(self, path: str, payload: bytes) -> str:
        """Write bytes and return the artifact URI/path."""

    @abstractmethod
    def read_bytes(self, path: str) -> bytes:
        """Read bytes from an artifact path."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Return whether an artifact path exists."""

    @abstractmethod
    def list(self, prefix: str = "") -> list[str]:
        """List artifact paths under a prefix."""


def create_artifact_store(
    backend: str | None = None,
    local_root: str | Path | None = None,
    bucket: str | None = None,
    prefix: str | None = None,
) -> ArtifactStore:
    """Create an artifact store from explicit arguments or environment."""

    selected_backend = (backend or os.getenv("MASS_ADK_ARTIFACT_BACKEND", "local")).lower()
    if selected_backend == "local":
        from .local_store import LocalArtifactStore

        root = local_root or os.getenv("MASS_ADK_LOCAL_ARTIFACT_ROOT", "artifacts")
        return LocalArtifactStore(root)
    if selected_backend == "gcs":
        from .gcs_store import GCSArtifactStore

        selected_bucket = bucket or os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
        if not selected_bucket:
            raise ValueError("GOOGLE_CLOUD_STORAGE_BUCKET is required for gcs artifact backend")
        selected_prefix = prefix or os.getenv("MASS_ADK_GCS_PREFIX", "mass-adk")
        return GCSArtifactStore(selected_bucket, selected_prefix)
    raise ValueError(f"Unsupported artifact backend: {selected_backend}")
