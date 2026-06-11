"""Local filesystem artifact store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .artifact_store import ArtifactStore


class LocalArtifactStore(ArtifactStore):
    """Path-safe local artifact store rooted at one directory."""

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        if Path(path).is_absolute():
            raise ValueError("Artifact paths must be relative")
        candidate = (self.root / path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Artifact path escapes root: {path}") from exc
        return candidate

    def write_json(self, path: str, payload: dict[str, Any]) -> str:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return str(target)

    def read_json(self, path: str) -> dict[str, Any]:
        target = self._resolve(path)
        return json.loads(target.read_text(encoding="utf-8"))

    def write_bytes(self, path: str, payload: bytes) -> str:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        return str(target)

    def read_bytes(self, path: str) -> bytes:
        return self._resolve(path).read_bytes()

    def exists(self, path: str) -> bool:
        return self._resolve(path).exists()

    def list(self, prefix: str = "") -> list[str]:
        base = self._resolve(prefix or ".")
        if not base.exists():
            return []
        if base.is_file():
            return [str(base.relative_to(self.root))]
        return sorted(
            str(item.relative_to(self.root)) for item in base.rglob("*") if item.is_file()
        )
