"""Runner wrapper for the integrated MASS engine snapshot."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from mass_engine import __version__
from mass_engine.cloud import create_artifact_store


MASS_ADK_ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = MASS_ADK_ROOT / "mass_engine"
DEFAULT_DATASET_ROOT = MASS_ADK_ROOT / "sample_data" / "ih_smoke"
DEFAULT_SP500_DATASET_ROOT = MASS_ADK_ROOT / "sample_data" / "sp500_smoke"
DEFAULT_LOCAL_ARTIFACT_ROOT = MASS_ADK_ROOT / "artifacts"


def load_runner_env() -> None:
    """Load MASS-ADK `.env` values while preserving explicit shell overrides."""

    load_dotenv(MASS_ADK_ROOT / ".env", override=False)


def _bool_env(name: str, *, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def build_run_id(args: argparse.Namespace) -> str:
    """Build a MASS-compatible run id for smoke experiments."""

    seed_suffix = f"seed{args.seed:02d}"
    return (
        f"{args.stock_pool}_{args.num_agents_per_investor}_{args.num_investor_type}_"
        f"{args.use_macro_data}_{args.use_agent_distribution_modification}_"
        f"{args.optimizer_look_back_window}_{args.allow_possible_data_leakage}_"
        f"{args.start_date}_{args.end_date}_{args.use_self_reflection}_"
        f"{args.optimizer}_{args.fitness_signal_col}_{args.learn_alpha}_"
        f"{args.turnover_penalty}_{seed_suffix}_std"
    )


def build_mass_command(args: argparse.Namespace, run_id: str) -> list[str]:
    """Build the copied MASS runtime command."""

    result_root = Path(args.result_root or DEFAULT_LOCAL_ARTIFACT_ROOT / "mass_engine" / "results")
    checkpoint_root = result_root / "checkpoints"
    return [
        sys.executable,
        "-m",
        "stock_disagreement.main",
        "--num_investor_type",
        str(args.num_investor_type),
        "--num_agents_per_investor",
        str(args.num_agents_per_investor),
        "--stock_pool",
        args.stock_pool,
        "--stock_num",
        str(args.stock_num),
        "--selected_stock_num",
        str(args.selected_stock_num),
        "--start_date",
        str(args.start_date),
        "--end_date",
        str(args.end_date),
        "--no-use_macro_data" if not args.use_macro_data else "--use_macro_data",
        "--no-use_agent_distribution_modification"
        if not args.use_agent_distribution_modification
        else "--use_agent_distribution_modification",
        "--no-use_self_reflection" if not args.use_self_reflection else "--use_self_reflection",
        "--optimizer",
        args.optimizer,
        "--fitness_signal_col",
        args.fitness_signal_col,
        "--learn_alpha" if args.learn_alpha else "--no-learn_alpha",
        "--turnover_penalty",
        str(args.turnover_penalty),
        "--max_agent_workers",
        str(args.max_agent_workers),
        "--request_timeout",
        str(args.request_timeout),
        "--seed",
        str(args.seed),
        "--dataset_root",
        str(args.dataset_root),
        "--sp500_dataset_root",
        str(args.sp500_dataset_root),
        "--result_root",
        str(result_root),
        "--checkpoint_root",
        str(checkpoint_root),
        "--dotenv_path",
        str(args.dotenv_path),
    ]


def build_manifest(args: argparse.Namespace, run_id: str, command: list[str]) -> dict[str, Any]:
    """Build a run manifest for local/GCS artifact inspection."""

    return {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "mass_adk_version": __version__,
        "mode": "smoke" if args.smoke else "custom",
        "status": "created",
        "artifact_backend": args.artifact_backend,
        "gcs_bucket": args.gcs_bucket,
        "gcs_prefix": args.gcs_prefix,
        "local_artifact_root": str(args.local_artifact_root),
        "adk_model": os.getenv("MASS_ADK_MODEL", "gemini-3.5-flash"),
        "engine_model": os.getenv("MASS_MODEL_NAME") or os.getenv("OPENAI_MODEL"),
        "engine_model_server_configured": bool(
            os.getenv("MASS_MODEL_SERVER") or os.getenv("OPENAI_BASE_URL")
        ),
        "google_cloud_project": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "google_cloud_location": os.getenv("GOOGLE_CLOUD_LOCATION", "global"),
        "engine_root": str(ENGINE_ROOT),
        "sample_data_root": str(MASS_ADK_ROOT / "sample_data"),
        "dataset_root": str(args.dataset_root),
        "sp500_dataset_root": str(args.sp500_dataset_root),
        "parameters": {
            "stock_pool": args.stock_pool,
            "num_investor_type": args.num_investor_type,
            "num_agents_per_investor": args.num_agents_per_investor,
            "stock_num": args.stock_num,
            "selected_stock_num": args.selected_stock_num,
            "start_date": args.start_date,
            "end_date": args.end_date,
            "optimizer": args.optimizer,
            "fitness_signal_col": args.fitness_signal_col,
            "learn_alpha": args.learn_alpha,
            "turnover_penalty": args.turnover_penalty,
            "seed": args.seed,
        },
        "command": command,
    }


def write_run_records(
    args: argparse.Namespace,
    run_id: str,
    manifest: dict[str, Any],
    progress: dict[str, Any],
) -> dict[str, str]:
    """Write run manifest and progress through the selected artifact store."""

    store = create_artifact_store(
        backend=args.artifact_backend,
        local_root=args.local_artifact_root,
        bucket=args.gcs_bucket,
        prefix=args.gcs_prefix,
    )
    base = f"runs/{run_id}"
    return {
        "manifest_uri": store.write_json(f"{base}/manifest.json", manifest),
        "progress_uri": store.write_json(f"{base}/progress.json", progress),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    load_runner_env()
    parser = argparse.ArgumentParser("Integrated MASS engine runner")
    parser.add_argument("--smoke", action="store_true", help="Use tiny validated smoke defaults")
    parser.add_argument("--execute", action="store_true", help="Execute copied MASS runtime instead of dry-run only")
    parser.add_argument("--artifact_backend", default=os.getenv("MASS_ADK_ARTIFACT_BACKEND", "local"), choices=["local", "gcs"])
    parser.add_argument("--local_artifact_root", default=os.getenv("MASS_ADK_LOCAL_ARTIFACT_ROOT", str(DEFAULT_LOCAL_ARTIFACT_ROOT)))
    parser.add_argument("--gcs_bucket", default=os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET"))
    parser.add_argument("--gcs_prefix", default=os.getenv("MASS_ADK_GCS_PREFIX", "mass-adk"))
    parser.add_argument("--dataset_root", default=os.getenv("MASS_ADK_DATASET_ROOT", str(DEFAULT_DATASET_ROOT)))
    parser.add_argument("--sp500_dataset_root", default=os.getenv("MASS_ADK_SP500_DATA_ROOT", os.getenv("MASS_ADK_SP500_DATASET_ROOT", str(DEFAULT_SP500_DATASET_ROOT))))
    parser.add_argument("--result_root", default=os.getenv("MASS_ADK_ENGINE_RESULT_ROOT", str(DEFAULT_LOCAL_ARTIFACT_ROOT / "mass_engine" / "results")))
    parser.add_argument("--dotenv_path", default=os.getenv("MASS_ADK_DOTENV_PATH", str(MASS_ADK_ROOT / ".env")))
    parser.add_argument("--stock_pool", default="ih", choices=["ih", "csi_300", "csi_500", "csi_1000", "start_up_100", "sp500"])
    parser.add_argument("--num_investor_type", type=int, default=2)
    parser.add_argument("--num_agents_per_investor", type=int, default=2)
    parser.add_argument("--stock_num", type=int, default=5)
    parser.add_argument("--selected_stock_num", type=int, default=2)
    parser.add_argument("--start_date", type=int, default=20230615)
    parser.add_argument("--end_date", type=int, default=20230620)
    parser.add_argument("--use_macro_data", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--use_agent_distribution_modification", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--use_self_reflection", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--optimizer_look_back_window", type=int, default=5)
    parser.add_argument("--allow_possible_data_leakage", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--optimizer", default="sa", choices=["sa", "cma_es"])
    parser.add_argument("--fitness_signal_col", default="Signal_std", choices=["Signal_std", "Signal"])
    parser.add_argument("--learn_alpha", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--turnover_penalty", type=float, default=0.0)
    parser.add_argument("--max_agent_workers", type=int, default=4)
    parser.add_argument("--request_timeout", type=float, default=90.0)
    parser.add_argument("--seed", type=int, default=1)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_id = build_run_id(args)
    command = build_mass_command(args, run_id)
    manifest = build_manifest(args, run_id, command)
    progress: dict[str, Any] = {
        "run_id": run_id,
        "status": "dry_run",
        "executed": False,
        "completed_at": None,
    }

    if args.execute:
        if not _bool_env("MASS_ADK_ENABLE_LIVE_RUNS"):
            progress["status"] = "blocked"
            progress["reason"] = "Set MASS_ADK_ENABLE_LIVE_RUNS=true to execute live MASS smoke runs."
            uris = write_run_records(args, run_id, manifest, progress)
            print(json.dumps({"run_id": run_id, "command": command, "records": uris, "progress": progress}, indent=2))
            return 2
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(ENGINE_ROOT) if not existing_pythonpath else f"{ENGINE_ROOT}:{existing_pythonpath}"
        result = subprocess.run(command, cwd=MASS_ADK_ROOT, env=env, check=False)
        progress.update(
            {
                "status": "completed" if result.returncode == 0 else "failed",
                "executed": True,
                "returncode": result.returncode,
                "completed_at": datetime.now(UTC).isoformat(),
            }
        )
        manifest["status"] = progress["status"]
    uris = write_run_records(args, run_id, manifest, progress)
    print(json.dumps({"run_id": run_id, "command": command, "records": uris, "progress": progress}, indent=2))
    return int(progress.get("returncode") or 0)


if __name__ == "__main__":
    raise SystemExit(main())
