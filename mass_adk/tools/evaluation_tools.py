"""Experiment evaluation and comparison tools."""

from __future__ import annotations

from typing import Any

from .manifest import get_comparison_by_id, get_experiment_by_id, load_manifest


def get_experiment_summary(experiment_id: str) -> dict[str, Any]:
    """Return the curated summary for one cached MASS experiment.

    Args:
        experiment_id: Experiment id from `list_available_experiments`.
    """

    experiment = get_experiment_by_id(experiment_id)
    if experiment is None:
        return {
            "error": f"Unknown experiment_id: {experiment_id}",
            "available_ids": [item["id"] for item in load_manifest()["experiments"]],
        }

    return {
        "experiment": experiment,
        "interpretation_guardrail": "Rank IC is a signal-quality metric, not a realized portfolio return.",
    }


def _parse_experiment_ids(experiment_ids: str) -> list[str]:
    return [part.strip() for part in experiment_ids.split(",") if part.strip()]


def compare_experiments(
    experiment_ids: str | None = None,
    comparison_id: str | None = None,
) -> dict[str, Any]:
    """Compare cached MASS experiments by explicit ids or curated comparison id.

    Args:
        experiment_ids: Comma-separated experiment ids.
        comparison_id: Curated comparison id, such as `china_512_scale`.
    """

    manifest = load_manifest()
    comparison = None
    selected_ids: list[str]

    if comparison_id:
        comparison = get_comparison_by_id(comparison_id)
        if comparison is None:
            return {
                "error": f"Unknown comparison_id: {comparison_id}",
                "available_comparison_ids": [
                    item["id"] for item in manifest["comparisons"]
                ],
            }
        selected_ids = comparison["experiment_ids"]
    elif experiment_ids:
        selected_ids = _parse_experiment_ids(experiment_ids)
    else:
        selected_ids = ["china_a_512_seed00", "china_e_512_seed00"]

    rows = []
    missing = []
    for experiment_id in selected_ids:
        experiment = get_experiment_by_id(experiment_id)
        if experiment is None:
            missing.append(experiment_id)
            continue
        metrics = experiment["metrics"]
        rows.append(
            {
                "id": experiment["id"],
                "label": experiment["label"],
                "market": experiment["market"],
                "config": experiment["config"],
                "agents": experiment["agents"],
                "optimizer": experiment["optimizer"],
                "fitness_signal_col": experiment["fitness_signal_col"],
                "learn_alpha": experiment["learn_alpha"],
                "turnover_penalty": experiment["turnover_penalty"],
                "seeds": len(experiment["seeds"]),
                "rank_ic_mean": metrics["rank_ic_mean"],
                "rank_ic_std": metrics["rank_ic_std"],
                "rank_icir": metrics["rank_icir"],
                "takeaway": experiment["takeaway"],
            }
        )

    best = None
    if rows:
        best = max(rows, key=lambda row: row["rank_ic_mean"])

    return {
        "comparison": comparison,
        "rows": rows,
        "missing_ids": missing,
        "best_by_rank_ic": best,
        "guardrails": [
            "Rank IC compares signal ranking quality, not realized portfolio returns.",
            "Single-seed rows should be treated as preliminary evidence.",
            "Human review is required before any investment or portfolio decision.",
        ],
    }
