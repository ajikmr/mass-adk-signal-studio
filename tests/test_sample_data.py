from pathlib import Path


def test_sample_macro_files_use_generic_names():
    expected = {
        "policy_rate.csv",
        "cpi_yoy.csv",
        "equity_index_pe_ttm.csv",
        "market_sentiment.csv",
        "ten_year_government_bond_yield.csv",
    }
    forbidden = {
        "China_1-Year_Loan_Prime_Rate_LPR.csv",
        "China_CPI_YoY_Current_Month.csv",
        "csi_300_pe_ttm.csv",
        "Market_Sentiment_Index.csv",
        "yield_on_China_10_year_government_bonds.csv",
    }

    for dataset in ["ih_smoke", "sp500_smoke"]:
        macro_root = Path("sample_data") / dataset / "macro_data"
        names = {path.name for path in macro_root.glob("*.csv")}
        assert expected.issubset(names)
        assert names.isdisjoint(forbidden)
