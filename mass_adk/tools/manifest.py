"""Manifest loading utilities for cached MASS experiment evidence."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from mass_adk.config import load_config


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    """Load the curated MASS experiment manifest."""

    manifest_path = load_config().manifest_path
    with manifest_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def get_experiment_by_id(experiment_id: str) -> dict[str, Any] | None:
    """Return one experiment from the manifest by id."""

    normalized = experiment_id.strip()
    for experiment in load_manifest()["experiments"]:
        if experiment["id"] == normalized:
            return experiment
    return None


def get_comparison_by_id(comparison_id: str) -> dict[str, Any] | None:
    """Return one curated comparison from the manifest by id."""

    normalized = comparison_id.strip()
    for comparison in load_manifest()["comparisons"]:
        if comparison["id"] == normalized:
            return comparison
    return None
