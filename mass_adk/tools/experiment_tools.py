"""Experiment listing and guarded live-run tools."""

from __future__ import annotations

from typing import Any

from mass_adk.config import load_config

from .manifest import load_manifest


def _matches(value: str | None, candidate: str) -> bool:
    return value is None or value.strip().lower() in candidate.lower()


def list_available_experiments(
    market: str | None = None,
    stock_pool: str | None = None,
) -> dict[str, Any]:
    """List cached MASS experiments, optionally filtered by market or stock pool.

    Args:
        market: Optional market filter, such as "China" or "US".
        stock_pool: Optional stock-pool filter, such as "ih" or "sp500".
    """

    experiments = []
    for experiment in load_manifest()["experiments"]:
        if not _matches(market, experiment["market"]):
            continue
        if stock_pool is not None and experiment["stock_pool"] != stock_pool:
            continue
        metrics = experiment["metrics"]
        experiments.append(
            {
                "id": experiment["id"],
                "label": experiment["label"],
                "market": experiment["market"],
                "stock_pool": experiment["stock_pool"],
                "window": experiment["window"],
                "config": experiment["config"],
                "agents": experiment["agents"],
                "seeds": experiment["seeds"],
                "rank_ic_mean": metrics["rank_ic_mean"],
                "rank_ic_std": metrics["rank_ic_std"],
                "takeaway": experiment["takeaway"],
            }
        )

    return {
        "experiments": experiments,
        "count": len(experiments),
        "filters": {"market": market, "stock_pool": stock_pool},
    }


def run_smoke_experiment(stock_pool: str | None = None) -> dict[str, Any]:
    """Describe or trigger the guarded tiny live-run path.

    Live MASS runs are disabled unless `MASS_ADK_ENABLE_LIVE_RUNS=true` is set.
    The default competition demo should use cached benchmark evidence instead.

    Args:
        stock_pool: Optional stock pool for a future tiny smoke run.
    """

    config = load_config()
    selected_pool = stock_pool or config.default_stock_pool
    command = (
        "PYTHONPATH=. python3 stock_disagreement/main.py "
        "--num_investor_type 2 --num_agents_per_investor 2 "
        f"--stock_pool {selected_pool} --stock_num 5 --selected_stock_num 2 "
        "--no-use_agent_distribution_modification --no-use_self_reflection "
        "--max_agent_workers 4 --request_timeout 90 --seed 1"
    )

    if not config.enable_live_runs:
        return {
            "status": "disabled",
            "reason": "Live MASS runs are disabled by MASS_ADK_ENABLE_LIVE_RUNS.",
            "recommended_demo_path": "Use cached experiments via list_available_experiments and compare_experiments.",
            "candidate_command": command,
        }

    return {
        "status": "not_executed",
        "reason": "Guard is enabled, but this tool intentionally does not launch shell commands in the ADK agent process yet.",
        "candidate_command": command,
    }
