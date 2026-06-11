"""Configuration helpers for MASS-ADK."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - keeps non-ADK utility tests lightweight.
    load_dotenv = None  # type: ignore[assignment]


APP_ROOT = Path(__file__).resolve().parents[1]
MASS_ROOT = APP_ROOT
DEFAULT_RESULTS_ROOT = APP_ROOT / "artifacts" / "mass_engine" / "results"
DEFAULT_MANIFEST_PATH = APP_ROOT / "mass_adk" / "data" / "experiment_manifest.json"


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration loaded from environment variables."""

    model: str
    mass_root: Path
    results_root: Path
    manifest_path: Path
    deploy_region: str
    default_stock_pool: str
    default_eval_label: int
    enable_live_runs: bool


def _as_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    return Path(value).expanduser().resolve()


def load_config(env_file: str | Path | None = None) -> AppConfig:
    """Load MASS-ADK configuration from `.env` and process environment."""

    if load_dotenv is not None:
        if env_file is not None:
            load_dotenv(Path(env_file))
        else:
            load_dotenv(APP_ROOT / ".env")

    return AppConfig(
        model=os.getenv("MASS_ADK_MODEL", "gemini-3.5-flash"),
        mass_root=_as_path(os.getenv("MASS_ADK_DATA_ROOT"), MASS_ROOT),
        results_root=_as_path(os.getenv("MASS_ADK_RESULTS_ROOT"), DEFAULT_RESULTS_ROOT),
        manifest_path=_as_path(
            os.getenv("MASS_ADK_MANIFEST_PATH"), DEFAULT_MANIFEST_PATH
        ),
        deploy_region=os.getenv("MASS_ADK_DEPLOY_REGION", "us-central1"),
        default_stock_pool=os.getenv("MASS_ADK_DEFAULT_STOCK_POOL", "sp500"),
        default_eval_label=int(os.getenv("MASS_ADK_DEFAULT_EVAL_LABEL", "10")),
        enable_live_runs=_as_bool(os.getenv("MASS_ADK_ENABLE_LIVE_RUNS")),
    )
