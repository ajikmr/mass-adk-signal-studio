"""Google Cloud Storage artifact store."""

from __future__ import annotations

import json
from typing import Any

from google.cloud import storage

from .artifact_store import ArtifactStore


class GCSArtifactStore(ArtifactStore):
    """GCS artifact store using bucket/prefix scoped object paths."""

    def __init__(self, bucket: str, prefix: str = "mass-adk"):
        self.bucket_name = bucket
        self.prefix = prefix.strip("/")
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket)

    def _blob_name(self, path: str) -> str:
        cleaned = path.strip("/")
        if ".." in cleaned.split("/"):
            raise ValueError(f"Artifact path escapes prefix: {path}")
        if not cleaned:
            return self.prefix
        return f"{self.prefix}/{cleaned}" if self.prefix else cleaned

    def _uri(self, path: str) -> str:
        return f"gs://{self.bucket_name}/{self._blob_name(path)}"

    def write_json(self, path: str, payload: dict[str, Any]) -> str:
        blob = self.bucket.blob(self._blob_name(path))
        blob.upload_from_string(
            json.dumps(payload, indent=2, sort_keys=True),
            content_type="application/json",
        )
        return self._uri(path)

    def read_json(self, path: str) -> dict[str, Any]:
        blob = self.bucket.blob(self._blob_name(path))
        return json.loads(blob.download_as_text())

    def write_bytes(self, path: str, payload: bytes) -> str:
        blob = self.bucket.blob(self._blob_name(path))
        blob.upload_from_string(payload)
        return self._uri(path)

    def read_bytes(self, path: str) -> bytes:
        blob = self.bucket.blob(self._blob_name(path))
        return blob.download_as_bytes()

    def exists(self, path: str) -> bool:
        return self.bucket.blob(self._blob_name(path)).exists()

    def list(self, prefix: str = "") -> list[str]:
        prefix_blob = self._blob_name(prefix)
        prefix_len = len(self.prefix) + 1 if self.prefix else 0
        return sorted(
            blob.name[prefix_len:]
            for blob in self.client.list_blobs(self.bucket_name, prefix=prefix_blob)
        )
