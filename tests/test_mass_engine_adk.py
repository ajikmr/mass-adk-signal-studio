from mass_engine_adk.tools import (
    DEMO_ALLOWED_STOCKS,
    get_demo_investor_decision_case,
    validate_investor_decision,
)


def test_demo_investor_decision_case_is_synthetic_and_bounded():
    case = get_demo_investor_decision_case()

    assert case["case_id"] == "synthetic_mass_investor_decision_v1"
    assert case["expected_stock_count"] == 2
    assert case["allowed_stocks"] == DEMO_ALLOWED_STOCKS
    assert len(case["features"]) == 4
    assert "Synthetic demo data" in case["safety_note"]


def test_validate_investor_decision_accepts_valid_selection():
    result = validate_investor_decision(["ALPHA", "BETA"])

    assert result["valid"] is True
    assert result["errors"] == []


def test_validate_investor_decision_rejects_illegal_and_wrong_count():
    result = validate_investor_decision(["ALPHA", "OMEGA", "ALPHA"])

    assert result["valid"] is False
    assert any("Expected 2" in error for error in result["errors"])
    assert any("Illegal stocks" in error for error in result["errors"])
    assert any("Duplicate stocks" in error for error in result["errors"])


def test_validate_investor_decision_parses_json_object():
    result = validate_investor_decision('{"Stock": ["ALPHA", "BETA"]}')

    assert result["valid"] is True
    assert result["selected_stocks"] == ["ALPHA", "BETA"]
