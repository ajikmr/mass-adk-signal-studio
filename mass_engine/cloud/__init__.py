"""Artifact-store backends for the integrated MASS engine."""

from .artifact_store import ArtifactStore, create_artifact_store
from .local_store import LocalArtifactStore

try:
    from .gcs_store import GCSArtifactStore
except ModuleNotFoundError:  # pragma: no cover - optional dependency guard.
    GCSArtifactStore = None  # type: ignore[assignment]

__all__ = [
    "ArtifactStore",
    "GCSArtifactStore",
    "LocalArtifactStore",
    "create_artifact_store",
]
