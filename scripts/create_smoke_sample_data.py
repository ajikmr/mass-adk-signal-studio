"""Create a tiny self-contained synthetic dataset for MASS-ADK smoke tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[1]
IH_ROOT = APP_ROOT / "sample_data" / "ih_smoke"
SP500_ROOT = APP_ROOT / "sample_data" / "sp500_smoke"

DATES = [20230615, 20230616, 20230619, 20230620]
STOCKS = [
    ("S001", "Alpha Materials", "Materials", 120.0),
    ("S002", "Beta Bank", "Financials", 220.0),
    ("S003", "Gamma Energy", "Energy", 180.0),
    ("S004", "Delta Health", "Healthcare", 150.0),
    ("S005", "Epsilon Tech", "Technology", 260.0),
]


def _make_market_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    stock_rows = []
    label_rows = []
    price_rows = []
    industry_rows = []
    for date_idx, date in enumerate(DATES):
        for stock_idx, (stock, name, industry, free_mv) in enumerate(STOCKS):
            base_price = 10.0 + stock_idx * 3.0 + date_idx * 0.2
            daily_return = ((stock_idx + 1) * 0.002) - (date_idx * 0.0005)
            close = round(base_price * (1 + daily_return), 4)
            stock_rows.append(
                {
                    "Stock": stock,
                    "Date": date,
                    "Open": round(base_price, 4),
                    "High": round(base_price * 1.015, 4),
                    "Low": round(base_price * 0.985, 4),
                    "Close": close,
                    "Value": round(1_000_000 + stock_idx * 80_000 + date_idx * 10_000, 2),
                    "FREE_MV": free_mv,
                }
            )
            label_rows.append(
                {
                    "Stock": stock,
                    "Date": date,
                    "1_15_labelB": round(0.01 * (stock_idx + 1) - 0.002 * date_idx, 6),
                    "5_15_labelB": round(0.015 * (stock_idx + 1) - 0.001 * date_idx, 6),
                    "10_15_labelB": round(0.02 * (stock_idx + 1) - 0.0015 * date_idx, 6),
                }
            )
            price_rows.append(
                {
                    "Stock": stock,
                    "Date": date,
                    "price_value_feature_0": round(0.10 + stock_idx * 0.03, 4),
                    "price_value_feature_1": round(0.20 + date_idx * 0.02, 4),
                    "price_value_feature_2": round(0.30 + stock_idx * 0.01, 4),
                    "price_value_feature_3": round(0.40 - date_idx * 0.015, 4),
                    "price_value_feature_4": round(0.50 - stock_idx * 0.02, 4),
                    "price_value_feature_5": round(0.60 + date_idx * 0.01, 4),
                }
            )
        for industry_idx, industry in enumerate(sorted({item[2] for item in STOCKS})):
            industry_rows.append(
                {
                    "Industry": industry,
                    "Daily_Return": round(0.001 * (industry_idx + 1) - date_idx * 0.0003, 6),
                }
            )
    return (
        pd.DataFrame(stock_rows),
        pd.DataFrame(label_rows),
        pd.DataFrame(price_rows),
        pd.DataFrame(industry_rows).drop_duplicates(),
    )


def _write_macro(root: Path) -> None:
    macro_root = root / "macro_data"
    macro_root.mkdir(parents=True, exist_ok=True)
    for old_file in macro_root.glob("*.csv"):
        old_file.unlink()
    macro_rows = pd.DataFrame(
        {
            "Date": DATES,
            "Value": [3.45, 3.45, 3.45, 3.45],
        }
    )
    macro_rows.to_csv(macro_root / "policy_rate.csv", index=False)
    pd.DataFrame({"Date": DATES, "Value": [0.2, 0.2, 0.3, 0.3]}).to_csv(
        macro_root / "cpi_yoy.csv", index=False
    )
    pd.DataFrame({"Date": DATES, "Value": [12.0, 12.1, 12.2, 12.3]}).to_csv(
        macro_root / "equity_index_pe_ttm.csv", index=False
    )
    pd.DataFrame({"Date": DATES, "PriceChange": [0.001, -0.002, 0.003, 0.001]}).to_csv(
        macro_root / "market_sentiment.csv", index=False
    )
    pd.DataFrame({"Date": DATES, "Value": [2.65, 2.66, 2.67, 2.66]}).to_csv(
        macro_root / "ten_year_government_bond_yield.csv", index=False
    )


def _write_dataset(root: Path, stock_pool_name: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    stock_df, label_df, price_df, industry_df = _make_market_frames()
    stock_basic = pd.DataFrame(
        [
            {"Stock": stock, "Name": name, "Industry": industry}
            for stock, name, industry, _free_mv in STOCKS
        ]
    )
    news_info = pd.DataFrame(
        {
            "Date": pd.Series(dtype="int32"),
            "NewsId": pd.Series(dtype="object"),
            "NewsTitle": pd.Series(dtype="object"),
            "Content": pd.Series(dtype="object"),
            "Source": pd.Series(dtype="object"),
        }
    )
    news_relationship = pd.DataFrame(
        {
            "Date": pd.Series(dtype="int32"),
            "Stock": pd.Series(dtype="object"),
            "NewsId": pd.Series(dtype="object"),
        }
    )

    stock_df.to_parquet(root / f"{stock_pool_name}.parq", index=False)
    stock_df.to_parquet(root / "base_data.parq", index=False)
    label_df.to_parquet(root / "all_ashare_label.parq", index=False)
    label_df.to_parquet(root / f"{stock_pool_name}_label.parq", index=False)
    stock_basic.to_parquet(root / "stock_basic_data.parq", index=False)
    industry_df.to_parquet(root / "industry_ret.parq", index=False)
    price_df.to_parquet(root / "price_feature.parq", index=False)
    news_info.to_parquet(root / "wind-financial-news-info.parq", index=False)
    news_relationship.to_parquet(root / "wind-financial-news-relationship.parq", index=False)
    _write_macro(root)


def main() -> None:
    _write_dataset(IH_ROOT, "ih")
    _write_dataset(SP500_ROOT, "sp500")
    print(f"Wrote smoke sample datasets under {APP_ROOT / 'sample_data'}")


if __name__ == "__main__":
    main()
