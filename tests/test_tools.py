from mass_adk.tools import (
    compare_experiments,
    generate_research_memo,
    get_experiment_summary,
    list_available_datasets,
    list_available_experiments,
    run_smoke_experiment,
)


def test_list_available_datasets():
    result = list_available_datasets()
    assert result["count"] >= 2
    assert any(dataset["stock_pool"] == "sp500" for dataset in result["datasets"])


def test_list_available_experiments_filters_sp500():
    result = list_available_experiments(stock_pool="sp500")
    assert result["count"] >= 2
    assert all(item["stock_pool"] == "sp500" for item in result["experiments"])


def test_get_experiment_summary_known_id():
    result = get_experiment_summary("china_a_64_multiseed")
    assert result["experiment"]["metrics"]["rank_ic_mean"] == 0.0331


def test_compare_china_512_scale():
    result = compare_experiments(comparison_id="china_512_scale")
    assert result["best_by_rank_ic"]["id"] == "china_e_512_seed00"
    assert len(result["rows"]) == 2


def test_generate_research_memo_contains_disclaimer():
    result = generate_research_memo(
        "512-agent scale comparison",
        comparison_id="china_512_scale",
    )
    assert "not financial advice" in result["markdown"]
    assert "china_e_512_seed00" in result["markdown"]


def test_smoke_run_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MASS_ADK_ENABLE_LIVE_RUNS", raising=False)
    result = run_smoke_experiment()
    assert result["status"] == "disabled"
