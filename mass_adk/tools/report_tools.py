"""Research memo generation helpers."""

from __future__ import annotations

from typing import Any

from .evaluation_tools import compare_experiments


DISCLAIMER = (
    "This memo is for research and educational use only. It is not financial "
    "advice, an investment recommendation, or an offer to buy or sell any "
    "security. Rank IC and ICIR are signal-quality metrics, not realized "
    "portfolio returns. Past signal quality does not guarantee future results. "
    "Human review is required before any investment decision."
)


def generate_research_memo(
    topic: str,
    comparison_id: str | None = None,
    experiment_ids: str | None = None,
) -> dict[str, Any]:
    """Generate a deterministic markdown memo from cached MASS evidence.

    Args:
        topic: Memo topic or audience framing.
        comparison_id: Optional curated comparison id.
        experiment_ids: Optional comma-separated experiment ids.
    """

    comparison = compare_experiments(
        experiment_ids=experiment_ids,
        comparison_id=comparison_id,
    )
    rows = comparison.get("rows", [])

    lines = [
        f"# MASS-ADK Research Memo: {topic}",
        "",
        "## Executive Read",
    ]
    if comparison.get("comparison"):
        lines.append(comparison["comparison"]["summary"])
    elif rows:
        best = comparison["best_by_rank_ic"]
        lines.append(
            f"Among the selected cached experiments, `{best['id']}` has the "
            f"highest 10-day Rank IC ({best['rank_ic_mean']})."
        )
    else:
        lines.append("No matching cached experiments were found.")

    lines.extend(["", "## Evidence Table", ""])
    lines.append(
        "| Experiment | Market | Agents | Optimizer | Seeds | 10d Rank IC | Takeaway |"
    )
    lines.append("| --- | --- | ---: | --- | ---: | ---: | --- |")
    for row in rows:
        rank_ic = row["rank_ic_mean"]
        if row["rank_ic_std"] is not None:
            rank_ic_text = f"{rank_ic:.4f} +/- {row['rank_ic_std']:.4f}"
        else:
            rank_ic_text = f"{rank_ic:.4f}"
        lines.append(
            "| "
            f"`{row['id']}` | {row['market']} | {row['agents']} | "
            f"{row['optimizer']} | {row['seeds']} | {rank_ic_text} | "
            f"{row['takeaway']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "MASS is best viewed as an upstream stock-ranking and signal-generation system. Its outputs should be paired with a separate portfolio-construction layer before comparing against direct allocators.",
            "",
            "## Caveats",
            "- Several 512-agent results are single-seed and should be treated as preliminary.",
            "- SP500 transfer evidence is positive but weaker than the China hero result.",
            "- The current evidence is about signal ranking quality, not realized trading performance.",
            "",
            "## Disclaimer",
            DISCLAIMER,
        ]
    )

    return {
        "topic": topic,
        "markdown": "\n".join(lines),
        "source_comparison": comparison,
    }
