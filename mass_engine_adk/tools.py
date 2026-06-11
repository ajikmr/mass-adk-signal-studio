"""Tools for the ADK-native MASS investor decision adapter."""

from __future__ import annotations

import json
from typing import Any


DEMO_ALLOWED_STOCKS = ["ALPHA", "BETA", "GAMMA", "DELTA"]


def get_demo_investor_decision_case() -> dict[str, Any]:
    """Return a tiny synthetic MASS investor-decision case.

    The data is synthetic and exists only to demonstrate an ADK-style investor
    decision step. It is not market data and should not be treated as investment
    advice.
    """

    return {
        "case_id": "synthetic_mass_investor_decision_v1",
        "expected_stock_count": 2,
        "allowed_stocks": DEMO_ALLOWED_STOCKS,
        "investor_style": {
            "risk_appetite": "moderate",
            "holding_period": "about one week",
            "preference": "prefer stronger value and stability features while avoiding high short-term volatility",
        },
        "features": [
            {
                "Stock": "ALPHA",
                "value_score": 0.82,
                "quality_score": 0.72,
                "momentum_score": 0.48,
                "volatility_score": 0.31,
            },
            {
                "Stock": "BETA",
                "value_score": 0.45,
                "quality_score": 0.88,
                "momentum_score": 0.61,
                "volatility_score": 0.29,
            },
            {
                "Stock": "GAMMA",
                "value_score": 0.76,
                "quality_score": 0.38,
                "momentum_score": 0.82,
                "volatility_score": 0.74,
            },
            {
                "Stock": "DELTA",
                "value_score": 0.33,
                "quality_score": 0.44,
                "momentum_score": 0.35,
                "volatility_score": 0.22,
            },
        ],
        "output_schema": {
            "Stock": "list[str] with exactly 2 symbols from allowed_stocks",
            "Rationale": "brief signal-style explanation",
            "Safety": "research/demo only; not financial advice",
        },
        "safety_note": "Synthetic demo data only. Do not treat output as a real investment recommendation.",
    }


def _parse_selected_stocks(selected_stocks: list[str] | str) -> list[str]:
    if isinstance(selected_stocks, list):
        return selected_stocks
    cleaned = selected_stocks.strip()
    if not cleaned:
        return []
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return [item.strip() for item in cleaned.split(",") if item.strip()]
    if isinstance(parsed, dict) and isinstance(parsed.get("Stock"), list):
        return parsed["Stock"]
    if isinstance(parsed, list):
        return parsed
    return []


def validate_investor_decision(
    selected_stocks: list[str] | str,
    allowed_stocks: list[str] | None = None,
    expected_count: int = 2,
) -> dict[str, Any]:
    """Validate selected stocks for a synthetic MASS investor-decision case.

    Args:
        selected_stocks: Selected symbols as a list, comma-separated string, JSON
            list string, or JSON object with a `Stock` list.
        allowed_stocks: Legal symbols. Defaults to the synthetic demo case.
        expected_count: Required number of selected symbols.
    """

    allowed = allowed_stocks or DEMO_ALLOWED_STOCKS
    selected = _parse_selected_stocks(selected_stocks)
    illegal = [stock for stock in selected if stock not in allowed]
    duplicates = sorted({stock for stock in selected if selected.count(stock) > 1})
    errors = []
    if len(selected) != expected_count:
        errors.append(f"Expected {expected_count} stocks, got {len(selected)}.")
    if illegal:
        errors.append(f"Illegal stocks: {illegal}.")
    if duplicates:
        errors.append(f"Duplicate stocks: {duplicates}.")

    return {
        "valid": not errors,
        "selected_stocks": selected,
        "allowed_stocks": allowed,
        "expected_count": expected_count,
        "errors": errors,
        "safety_note": "Validation checks symbol legality only. It does not validate investment quality or provide financial advice.",
    }
