import json
import os
from enum import IntFlag 
from pathlib import Path
from typing import *

import numpy as np
import pandas as pd
from openai import OpenAI
from scipy.stats import percentileofscore  

from stock_disagreement import OpenAIModel
from stock_disagreement.agent import RandomStockSelector, BasicStockSelector, IndustryBasisStockSelector, IndustryEqualStockSelector, MVEqualStockSelector
from stock_disagreement.agent.investment_analyzer import InvestmentAnalyzer
from stock_disagreement.agent.investing_history import InvestingHistory
from stock_disagreement.prompts import (INVESTING_DECISION_EXAMPLE, 
                                        INVESTING_DECISION_INSTRUCTION, 
                                        INVESTING_STYLE_INSTRUCTION,
                                        INVSETING_STYLE_EXAMPLE, 
                                        INVESTING_DECISION_INSTRUCTION_USING_SELF_REFLECTION,
                                        INVESTING_STYLE_INSTRUCTION_WITH_MARCO_DATA,
                                        INVESTING_STYLE_WITH_MACRO_DATA_EXAMPLE)

MAX_RETRIRES = 3
MASS_ADK_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = MASS_ADK_ROOT / "sample_data" / "ih_smoke"


def load_dotenv_file(dotenv_path: str | None = None) -> None:
    candidate_paths = []
    if dotenv_path:
        candidate_paths.append(dotenv_path)
    candidate_paths.append(os.getenv("MASS_ADK_DOTENV_PATH"))
    candidate_paths.append(str(MASS_ADK_ROOT / ".env"))
    candidate_paths.append(str(MASS_ADK_ROOT / "mass_engine" / "stock_disagreement" / ".env"))
    for path in candidate_paths:
        if not path or not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)
        break


def resolve_llm_config(dotenv_path: str | None = None) -> tuple[str, str, str]:
    load_dotenv_file(dotenv_path)
    model_name = os.getenv("MASS_MODEL_NAME", os.getenv("OPENAI_MODEL", "gpt-5.4"))
    model_server = os.getenv("MASS_MODEL_SERVER", os.getenv("OPENAI_BASE_URL", ""))
    api_key = os.getenv("MASS_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    if not model_server or not api_key:
        raise ValueError(
            "Missing MASS LLM configuration. Set MASS_MODEL_SERVER and MASS_API_KEY "
            "in the environment or in a .env file."
        )
    return model_name, model_server, api_key

def calculate_pe_quantile_5y(df:pd.DataFrame) -> pd.DataFrame:  
    

    df_copy = df.copy()  
    df_copy["dt"] = pd.to_datetime(df_copy["Date"].astype(str), format="%Y%m%d")   
    df_copy.sort_values("dt", inplace=True)  
    df_copy.reset_index(drop=True, inplace=True)  
    
    min_periods = 10 * 250  
    df_copy["quantile"] = df_copy["Value"].rolling(  
        window= min_periods, closed="both"  
    ).apply(lambda x: percentileofscore(x, x.iloc[-1]), raw=False)  
    
    df_copy["quantile"] = df_copy["quantile"].round(1)  
    
    df_copy["Date"] = df_copy["dt"].dt.strftime("%Y%m%d").astype(int)  
    return df_copy[["Date", "Value", "quantile"]]  

class Modality(IntFlag):  
    FUDAMENTAL_VALUTION = 0b00000001  
    FUDAMENTAL_DIVIDEND = 0b00000010 
    FUDAMENTAL_GROWTH = 0b000000100
    FUDAMENTAL_QUALITY = 0b000001000
    NEWS = 0b000010000      
    BASE_DATA = 0b000100000  
    CROSS_INDUSTRY_LABEL = 0b001000000
    RISK_FACTOR = 0b010000000
    PRICE_FEATURE = 0b100000000 




class StockDisagreementAgent():
    system_prompt: str = "You are a helpful assistant. Strictly follow the user's input prompt and output the result in JSON format as specified. Do not include any additional content."

    def __init__(self, 
                 stock_num: int, 
                 stock_pool: pd.DataFrame,
                 stock_labels: pd.DataFrame,
                 csi_300_pe: pd.DataFrame,
                 cpi: pd.DataFrame,
                 loan_rate: pd.DataFrame,
                 yield_on_China_bonds: pd.DataFrame,
                 market_sentiment_index: pd.DataFrame,
                 is_self_reflective: bool = False,
                 max_reflective_times: int = 10,
                 start_date: int | None = None,
                 end_date: int | None = None,
                 modality: Modality = Modality.FUDAMENTAL_VALUTION,
                 use_prev_stock: bool = False,
                 use_self_reflection: bool = False,
                 use_macro_data: bool = False,
                 dataset_dir: str = None,
                   stock_pool_name: str = "ih",
                  request_timeout: float = 120.0,
                 dotenv_path: str | None = None,
                  agent_id: str | None = None,
                   ):
        self.model_name, self.model_server, self.api_key = resolve_llm_config(dotenv_path)
        self.client = OpenAI(api_key=self.api_key, base_url=self.model_server, timeout=request_timeout)
        self.model = OpenAIModel(self.model_name, None, 80000)
        self.agent_id = agent_id or f"agent_{int(modality)}"
        self.stock_num = stock_num
        self.stock_pool = stock_pool
        self.stock_labels = stock_labels
        self.is_self_reflective = is_self_reflective
        self.max_reflective_times = max_reflective_times
        self.loan_rate = loan_rate
        self.cpi = cpi
        self.market_sentiment_index = market_sentiment_index
        self.csi_300_pe = csi_300_pe
        self.yield_on_China_bonds = yield_on_China_bonds
        self.csi_300_pe = calculate_pe_quantile_5y(csi_300_pe)

        self.csi_300_pe["Date"] = self.csi_300_pe["Date"].astype("int32")

        self.cpi["Date"] = self.cpi["Date"].astype("int32")

        self.yield_on_China_bonds["Date"] = pd.to_datetime(self.yield_on_China_bonds["Date"].astype(str))
        self.yield_on_China_bonds["Date"] = self.yield_on_China_bonds["Date"].dt.strftime("%Y%m%d").astype("int32")
        self.yield_on_China_bonds = self.yield_on_China_bonds.sort_values("Date")
        self.yield_on_China_bonds["1_day_diff"] = self.yield_on_China_bonds["Value"].diff(periods=1)
        self.yield_on_China_bonds["30_day_diff"] = self.yield_on_China_bonds["Value"].diff(periods=30)
        self.yield_on_China_bonds["180_day_diff"] = self.yield_on_China_bonds["Value"].diff(periods=180)
        self.yield_on_China_bonds[["1_day_diff", "30_day_diff", "180_day_diff"]] = self.yield_on_China_bonds[
            ["1_day_diff", "30_day_diff", "180_day_diff"]
        ].fillna(0.0)

        self.loan_rate["Date"] = self.loan_rate["Date"].astype("int32")

        self.market_sentiment_index["Date"] = self.market_sentiment_index["Date"].astype("int32")


        if start_date is None:
            self.start_date = stock_pool["Date"].min()
        else:
            self.start_date = start_date
        if end_date is None:
            self.end_date = stock_pool["Date"].max()
        else:
            self.end_date = end_date
        self.modality = modality
        self.prepare_data: dict[str, pd.DataFrame] = {}
        self.description: dict[str, str] = {}
        self.strategy_input: str = ""
        # self.prepare_data_source()
        self.strategy: dict[str, Any] = None
        self.stock_selector: BasicStockSelector = None
        self.use_macro_data = use_macro_data
        self.investment_analyzer = InvestmentAnalyzer()
        self.prev_stock: list[str] | None = None
        self.investing_history = InvestingHistory()
        self.use_prev_stock = use_prev_stock
        self.use_self_reflection = use_self_reflection
        self.dataset_dir = dataset_dir if dataset_dir else os.getenv("MASS_ADK_DATASET_ROOT", str(DEFAULT_DATASET_ROOT))
        self.stock_pool_name = stock_pool_name

    def export_runtime_state(self) -> dict[str, Any]:
        selector_name = None
        if self.stock_selector is not None:
            selector_name = self.stock_selector.__class__.__name__
        return {
            "strategy": self.strategy,
            "selector_name": selector_name,
            "prev_stock": self.prev_stock,
            "history_records": list(self.investing_history.records),
            "history_stock_list": list(self.investing_history.history_stock_list),
            "chosen_stock_list": list(self.investing_history.chosen_stock_list),
        }

    def load_runtime_state(self, state: dict[str, Any] | None) -> None:
        if not state:
            self.strategy = None
            self.stock_selector = None
            self.prev_stock = None
            self.investing_history = InvestingHistory()
            return
        self.strategy = state.get("strategy")
        selector_name = state.get("selector_name")
        if selector_name:
            self.stock_selector = self._build_selector(selector_name)
        else:
            self.stock_selector = None
        self.prev_stock = state.get("prev_stock")
        self.investing_history = InvestingHistory()
        self.investing_history.records.extend(state.get("history_records", []))
        self.investing_history.history_stock_list.extend(state.get("history_stock_list", []))
        self.investing_history.chosen_stock_list.extend(state.get("chosen_stock_list", []))

    def _strip_markdown_fence(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        return cleaned.strip()

    def _build_selector(self, selector_name: str) -> BasicStockSelector:
        if selector_name == "IndustryEqualStockSelector":
            return IndustryEqualStockSelector(self.stock_num, self.stock_pool, self.start_date, self.end_date)
        if selector_name == "MVEqualStockSelector":
            return MVEqualStockSelector(self.stock_num, self.stock_pool, self.start_date, self.end_date)
        if selector_name == "IndustryBasisStockSelector":
            return IndustryBasisStockSelector(self.stock_num, self.stock_pool, self.start_date, self.end_date, [])
        return RandomStockSelector(self.stock_num, self.stock_pool, self.start_date, self.end_date)

    def generate_macro_data_input(self, date: int) -> str:
        latest_loan_rate_date = self.loan_rate[self.loan_rate["Date"] <= date]["Date"].max()
        latest_loan_rate = self.loan_rate[self.loan_rate["Date"] == latest_loan_rate_date]["Value"].iloc[0]
        res = ""
        
        if self.stock_pool_name == "sp500":
            res += f"The latest Fed Funds rate is {str(latest_loan_rate)}. "
            
            latest_cpi_rate_date = self.cpi[self.cpi["Date"] <= date]["Date"].max()
            latest_cpi = self.cpi[self.cpi["Date"] == latest_cpi_rate_date]["Value"].iloc[0]
            res += f"The latest month US CPI YOY growth rate is {str(latest_cpi)}. "
            
            latest_yield_on_China_bonds_date = self.yield_on_China_bonds[self.yield_on_China_bonds["Date"] <= date]["Date"].max()
            latest_yield = self.yield_on_China_bonds[self.yield_on_China_bonds["Date"] == latest_yield_on_China_bonds_date]["Value"].iloc[0]
            one_day_yield_diff = self.yield_on_China_bonds[self.yield_on_China_bonds["Date"] == latest_yield_on_China_bonds_date]["1_day_diff"].iloc[0]
            month_yield_diff = self.yield_on_China_bonds[self.yield_on_China_bonds["Date"] == latest_yield_on_China_bonds_date]["30_day_diff"].iloc[0]
            half_year_yield_diff = self.yield_on_China_bonds[self.yield_on_China_bonds["Date"] == latest_yield_on_China_bonds_date]["180_day_diff"].iloc[0]
            res += f"The latest yield of US ten year Treasury bonds is {str(latest_yield)}%, while yield increases {str(round(one_day_yield_diff * 100))} BP over past one day, increases {str(round(month_yield_diff * 100))} BP over past one month, increases {str(round(half_year_yield_diff * 100))} BP over past half an year. "
            
            latest_pe_date = self.csi_300_pe[self.csi_300_pe["Date"] <= date]["Date"].max()
            latest_pe = self.csi_300_pe[self.csi_300_pe["Date"] == latest_pe_date]["Value"].iloc[0]
            latest_pe_quantile = self.csi_300_pe[self.csi_300_pe["Date"] == latest_pe_date]["quantile"].iloc[0]
            res += f"The latest S&P 500 PE is {str(latest_pe)}, and the current PE ratio of the S&P 500 is at the {latest_pe_quantile} percentile over the past 5 years(0 indicates most undervalued, and 100 indicates most overvalued). "
        else:
            res += f"The latest 1 year loan prime rate is {str(latest_loan_rate)}. "
            
            latest_cpi_rate_date = self.cpi[self.cpi["Date"] <= date]["Date"].max()
            latest_cpi = self.cpi[self.cpi["Date"] == latest_cpi_rate_date]["Value"].iloc[0]
            res += f"The latest month China CPI YOY growth rate is {str(latest_cpi)}. "
            
            latest_yield_on_China_bonds_date = self.yield_on_China_bonds[self.yield_on_China_bonds["Date"] <= date]["Date"].max()
            latest_yield = self.yield_on_China_bonds[self.yield_on_China_bonds["Date"] == latest_yield_on_China_bonds_date]["Value"].iloc[0]
            one_day_yield_diff = self.yield_on_China_bonds[self.yield_on_China_bonds["Date"] == latest_yield_on_China_bonds_date]["1_day_diff"].iloc[0]
            month_yield_diff = self.yield_on_China_bonds[self.yield_on_China_bonds["Date"] == latest_yield_on_China_bonds_date]["30_day_diff"].iloc[0]
            half_year_yield_diff = self.yield_on_China_bonds[self.yield_on_China_bonds["Date"] == latest_yield_on_China_bonds_date]["180_day_diff"].iloc[0]
            res += f"The latest yield of China ten year government bonds is {str(latest_yield)}%, while yield increases {str(round(one_day_yield_diff * 100))} BP over past one day, increases {str(round(month_yield_diff * 100))} BP over past one month, increases {str(round(half_year_yield_diff * 100))} BP over past half an year. "
            
            latest_pe_date = self.csi_300_pe[self.csi_300_pe["Date"] <= date]["Date"].max()
            latest_pe = self.csi_300_pe[self.csi_300_pe["Date"] == latest_pe_date]["Value"].iloc[0]
            latest_pe_quantile = self.csi_300_pe[self.csi_300_pe["Date"] == latest_pe_date]["quantile"].iloc[0]
            res += f"The latest csi_300 pe is {str(latest_pe)}, and the current PE ratio of the CSI 300 is at the {latest_pe_quantile} percentile over the past 5 years(0 indicates most undervalued, and 100 indicates most overvalued). "
        
        market_sentiment_index_date = self.market_sentiment_index[self.market_sentiment_index["Date"] <= date]["Date"].max()
        market_sentiment_index_pricechange = self.market_sentiment_index[self.market_sentiment_index["Date"] == market_sentiment_index_date]["PriceChange"].iloc[0]
        res += f"The latest market sentiement index got {str(round( market_sentiment_index_pricechange * 100, 2))} % return."
        
        return res
        
   
    def prepare_data_source(self, news_info: pd.DataFrame, news_relationship: pd.DataFrame) -> None:
        if self.modality & Modality.FUDAMENTAL_VALUTION:
            keys = ["E/P", "B/P", "CF/P", "S/P",
                    "Log-orthogonalized E/P", "Log-orthogonalized B/P",
                    "Log-orthogonalized CF/P", "Log-orthogonalized S/P", "EBITDA/EV"]
            
            self.prepare_data["fudamental_valuation"] = pd.read_parquet(f"{self.dataset_dir}/sub_fudamental_data.parq")[["Stock", "Date"] + keys]
            self.description["E/P"] = "The inverse of the P/E ratio (E/P) indicates the earnings yield, showing the percentage of profit generated per dollar invested in the stock."
            self.description["B/P"] = "Inverse of P/B (B/P) indicates the book yield, showing the return on book value per dollar invested."
            self.description["S/P"] = "Inverse of P/S (S/P) reflects the sales yield, showing sales generated per dollar invested."
            self.description["CF/P"] = "Inverse of P/CF (CF/P) shows the cash flow yield, representing cash flow generated per dollar invested."
            self.description["Log-orthogonalized E/P"] = "Log-orthogonalized version of E/P, removing some kind of cap basis.Log-orthogonalized version of E/P, removing some kind of cap basis."
            self.description["Log-orthogonalized B/P"] = "Log-orthogonalized version of B/P, removing some kind of cap basis."
            self.description["Log-orthogonalized CF/P"] = "Log-orthogonalized version of CF/P, removing some kind of cap basis."
            self.description["Log-orthogonalized S/P"] = "Log-orthogonalized version of S/P, removing some kind of cap basis."
            self.description["EBITDA/EV"] = "Measures a company's return on enterprise value, indicating operating earnings (EBITDA) generated per dollar of EV."
        
        if self.modality & Modality.FUDAMENTAL_QUALITY:
            keys = ["ROE stability", "ROA stability", "ROE", "Annualized ROE"]
            self.prepare_data["fudamental_quality"] = pd.read_parquet(f"{self.dataset_dir}/sub_fudamental_data.parq")[["Stock", "Date"] + keys]
            self.description["ROE"] = "ROE Measures profitability, showing net income generated per dollar of shareholders' equity."
            self.description["ROE stability"] = "TS_Mean(ROE, 8) / TS_Std(ROE, 8), measuring both absolute value and stability of ROE."
            self.description["ROA stability"] = "TS_Mean(ROA, 8) / TS_Std(ROA, 8), measuring both absolute value and stability of ROA."
            self.description["Annualized ROE"] = "Annualized version of ROE."
        
        if self.modality & Modality.FUDAMENTAL_DIVIDEND:
            keys = ["Dividend yield", "Log-orthogonalized dividend yield", "Log-orthogonalized dividend yield", "Dividend yield incl repo & mjrholder trans"]
            self.prepare_data["fudamental_dividend"] = pd.read_parquet(f"{self.dataset_dir}/sub_fudamental_data.parq")[["Stock", "Date"] + keys]
            self.description["Dividend yield"] = "Dividend yield indicates annual dividends received per dollar invested, expressed as a percentage of the stock price"
            self.description["Log-orthogonalized dividend yield"] = "Log-orthogonalized version of dividend yield, removing some kind of cap basis."
            self.description["Dividend yield incl repo & mjrholder trans"] = "Dividend yield including stock repurchasing and major holder trading."
        
        if self.modality & Modality.FUDAMENTAL_GROWTH:
            keys = ["Revenue TTM YoY growth rate", "Net profit TTM YoY growth rate", "Non-GAAP net profit YoY growth rate"]
            self.prepare_data["fudamental_growth"] = pd.read_parquet(f"{self.dataset_dir}/sub_fudamental_data.parq")[["Stock", "Date"] + keys]
            self.description["Revenue TTM YoY growth rate"] = "Measures the percentage change in trailing twelve months' revenue compared to the same period last year."
            self.description["Net profit TTM YoY growth rate"] = "Measures the percentage change in trailing twelve months' net profit compared to the same period last year."
            self.description["Non-GAAP net profit YoY growth rate"] = "Indicates the percentage change in non-GAAP net profit compared to the same period last year."
        
        if self.modality & Modality.RISK_FACTOR:
            keys = ["Intraday volatility", "Liquidity", "Residual volatility"]
            self.prepare_data["risk_factor"] = pd.read_parquet(f"{self.dataset_dir}/sub_fudamental_data.parq")[["Stock", "Date"] + keys]
            self.description["Intraday volatility"] = "Measuring the price fluctuation range of a stock within a single trading day."
            self.description["Liquidity"] = "Weighted average of monthly, quarterly and yearly turnover ratio."
            self.description["Residual volatility"] = "Residual volatility measures the unexplained variability in a security's returns after accounting for market or factor influences, indicating idiosyncratic risk."

        
        if self.modality & Modality.BASE_DATA:
            keys = ["Open", "High", "Low", "Close", "Value"]
            self.prepare_data["base_data"] = pd.read_parquet(f"{self.dataset_dir}/base_data.parq")[["Stock", "Date"] + keys]
        
        if self.modality & Modality.CROSS_INDUSTRY_LABEL:
            keys = ["Industry", "Daily_Return"]
            self.prepare_data["cross_industry_label"] = pd.read_parquet(f"{self.dataset_dir}/industry_ret.parq")[keys]
            self.prepare_data["stock_basic_data"] = pd.read_parquet(f"{self.dataset_dir}/stock_basic_data.parq")
            self.description["Daily_Return"] = "One-day return of holding the sector's constituent stocks."
        
        if self.modality & Modality.PRICE_FEATURE:
            keys = ["price_value_feature_0", "price_value_feature_1", "price_value_feature_2",
                    "price_value_feature_3", "price_value_feature_4", "price_value_feature_5"]
            
            self.prepare_data["price_value_data"] = pd.read_parquet(f"{self.dataset_dir}/price_feature.parq")[["Stock", "Date"] + keys]
            self.description["price_value_feature_0"] = "Combined feature using price and value data, theoretically negatively correlated with future daily returns over the next 1-5 days."
            self.description["price_value_feature_1"] = "Combined feature using price and value data, theoretically negatively correlated with future daily returns over the next 1-5 days."
            self.description["price_value_feature_2"] = "Combined feature using price and value data, theoretically negatively correlated with future daily returns over the next 1-5 days."
            self.description["price_value_feature_3"] = "Combined feature using price and value data, theoretically positively correlated with future daily returns over the next 1-5 days."
            self.description["price_value_feature_4"] = "Combined feature using price and value data, theoretically negatively correlated with future daily returns over the next 1-5 days."
            self.description["price_value_feature_5"] = "Combined feature using price and value data, theoretically possitively correlated with future daily returns over the next 1-5 days."
        
        if self.modality & Modality.NEWS:
            news_info = news_info
            news_relationship = news_relationship.merge(self.stock_pool[["Stock", "Date"]], on=["Stock", "Date"])
            self.prepare_data["news"] = news_info[["Date", "NewsId", "NewsTitle"]].merge(news_relationship[["Stock","NewsId"]], on=["NewsId"])
            # self.prepare_data["news"] = news_info.iloc[:, ~self.prepare_data["news"].columns.isin(["NewsId"])]


    def generate_strategy_input(self, date: int = None) -> tuple[str, str]: 
        def generate_headers() -> dict[str, str]:
            res = {}
            for key, description in self.description.items():
                res[key] = description
            if "news" in self.prepare_data.keys():
                res["news"] = f"Investors read news to make investment descisions. The example news is: {self.prepare_data['news']['NewsTitle'].head(3).to_list()}"
            return res
        headers = generate_headers()
        input = f"Investors read following information to make investment decisions. The information is in key-value format, key representing name, value representing descriptions.: \
                 {str(headers)}. \n"
        if date is None:
            return input, None
        macro_input = self.generate_macro_data_input(date) 
        return input, macro_input
    
    def genererate_self_reflection_input(self, date:int) -> dict[str, Any]:
        def get_stock_labels(date: int, x: int, stock_labels: pd.DataFrame) -> Tuple[bool, pd.DataFrame]:
            if x <= 0:
                raise ValueError(f"{x} is expected to be positive integers.")
            stock_labels = stock_labels.sort_values("Date")
            sorted_dates = np.sort(stock_labels["Date"].unique())
            idx = np.searchsorted(sorted_dates, date, side="left")
            target_idx = idx - x
            if target_idx < 0:
                return False, None
            target_date = sorted_dates[target_idx]
            target_data = stock_labels[stock_labels["Date"] == target_date]
            success = len(target_data) > 0
            return success, target_data
        res_dict = {}
        pass_days = [1, 5, 10]
        for pass_day in pass_days:
            success, pass_stock_labels = get_stock_labels(date, pass_day, self.stock_labels)
            if not success:
                break
            success, pass_stock_list = self.investing_history.get_history_stocks(pass_day)
            if not success:
                break
            success, chosen_stock_list = self.investing_history.get_chosen_stocks(pass_day)
            if not success:
                break
            success, pass_investing_history = self.investing_history.get_record(pass_day)
            if not success:
                break
            current_dict = {}
            current_dict["description"] = f"Investing history {pass_day} ago."
            current_dict["input_data"] = pass_investing_history
            sub_stock_label = pass_stock_labels[pass_stock_labels["Stock"].isin(pass_stock_list)].copy()
            sub_stock_label["rank"] = sub_stock_label[f"{pass_day}_15_labelB"].rank(ascending=False, method="min")
            investment_res = ""
            for stock in chosen_stock_list:
                if stock in pass_stock_list:
                    if stock in sub_stock_label["Stock"].unique().tolist():
                        investment_res += f"For chosen stock {stock}, you get rank {sub_stock_label[sub_stock_label['Stock'] == stock]['rank'].iloc[0].astype(int)} out of {len(pass_stock_list)}."
            current_dict["investment_res"] = investment_res
            res_dict[f"{pass_day} ago"] = current_dict
        return res_dict

    def generate_strategy_and_stock_selector(self, date: int = None) -> tuple[dict[str, Any], str, str]:
        data_input, macro_input = self.generate_strategy_input(date)
        if not self.use_macro_data:
            strategy_input = INVESTING_STYLE_INSTRUCTION.format(examples=INVSETING_STYLE_EXAMPLE, input_data=data_input)
        else:
            strategy_input = INVESTING_STYLE_INSTRUCTION_WITH_MARCO_DATA.format(examples=INVESTING_STYLE_WITH_MACRO_DATA_EXAMPLE,
                                                                                input_data=data_input,
                                                                                macro_data=macro_input)
        strategy,_ = self.model.chat_generate(client=self.client,
                                       system_prompt=self.system_prompt,
                                       input_string=strategy_input
                                       )
        # Robust JSON parsing with retry
        for attempt in range(3):
            try:
                cleaned = self._strip_markdown_fence(strategy)
                json_strategy = json.loads(cleaned)
                break
            except json.JSONDecodeError:
                if attempt < 2:
                    strategy,_ = self.model.chat_generate(client=self.client,
                                                   system_prompt=self.system_prompt,
                                                   input_string=strategy_input
                                                   )
                else:
                    # Fallback: use a default strategy
                    print(f"[WARN] Failed to parse strategy JSON after 3 attempts, using default. Response: {strategy[:200]}")
                    json_strategy = {"Details": {"StockPoolSelector": "RandomStockSelector"}, "Strategy": "default random selection"}
        selector_name = json_strategy["Details"]["StockPoolSelector"]
        if not isinstance(selector_name, str):
            print("stock selector does not match, using default random stock selector.")
            selector_name = "RandomStockSelector"
        stock_selector = self._build_selector(selector_name)
        assert isinstance(stock_selector, BasicStockSelector)
        self.strategy = json_strategy
        self.stock_selector = stock_selector
        return json_strategy, strategy, selector_name

    def _build_investment_prompt(self, date: int, current_stock: list[str], num_stocks: int) -> tuple[str, str]:
        prepare_datas = {}
        descriptions = {}
        for key in self.prepare_data:
            if "Stock" in self.prepare_data[key].columns and "Date" in self.prepare_data[key].columns:
                prepare_datas[key] = self.prepare_data[key][(self.prepare_data[key]["Date"] == date) & (self.prepare_data[key]["Stock"].isin(current_stock))]
            elif "Stock" in self.prepare_data[key].columns:
                prepare_datas[key] = self.prepare_data[key][(self.prepare_data[key]["Stock"].isin(current_stock))]
        for key in self.description:
            descriptions[key] = self.description[key]
        input_data = f"Input Data for investing decision:1. descriptions: {str(descriptions)}, 2. input data: {str(prepare_datas)}."
        investment_strategy = f" Investment strategy: {str(self.strategy)}"
        if not self.use_self_reflection:
            llm_input = INVESTING_DECISION_INSTRUCTION.format(num_stocks=num_stocks, examples=INVESTING_DECISION_EXAMPLE, input_data=input_data + investment_strategy)
        else:
            reflection_input = self.genererate_self_reflection_input(date)
            llm_input = INVESTING_DECISION_INSTRUCTION_USING_SELF_REFLECTION.format(
                num_stocks=num_stocks,
                examples=INVESTING_DECISION_EXAMPLE,
                input_data=input_data + investment_strategy,
                decision_history=str(reflection_input),
            )
        return input_data, llm_input

    def run_investment_task(self, date: int, num_stocks: int) -> dict[str, Any]:
        strategy, strategy_raw, selector_name = self.generate_strategy_and_stock_selector(date)
        current_stock = self.stock_selector.select_stock_for_llm(date=date)
        input_data, llm_input = self._build_investment_prompt(date, current_stock, num_stocks)
        selected_stocks: list[str] = []
        decision_raw = None
        error = None
        for attempt in range(MAX_RETRIRES):
            try:
                decision_raw, _ = self.model.chat_generate(
                    client=self.client,
                    system_prompt=self.system_prompt,
                    input_string=llm_input,
                )
                cleaned = self._strip_markdown_fence(decision_raw)
                selected_stocks = json.loads(cleaned)["Stock"]
                print(f"on {date}, agent {self.modality} chooses {str(selected_stocks)}")
                for stock in selected_stocks:
                    if stock not in current_stock:
                        print(f"current stock is {str(current_stock)}, whereas current selected stock is {stock}")
                        raise ValueError(f"LLM output illegal stock code {stock}!")
                break
            except Exception as exc:
                error = str(exc)
                print(f"occuring exceptions {error} in investment decisions")
                if attempt >= MAX_RETRIRES - 1:
                    print("Exceeding max retries, giving up.")
                    return {
                        "status": "failed",
                        "agent_id": self.agent_id,
                        "modality": int(self.modality),
                        "date": date,
                        "strategy": strategy,
                        "strategy_raw": strategy_raw,
                        "selector_name": selector_name,
                        "current_stock": current_stock,
                        "selected_stocks": [],
                        "decision_raw": decision_raw,
                        "input_data": input_data,
                        "error": error,
                    }
        return {
            "status": "success",
            "agent_id": self.agent_id,
            "modality": int(self.modality),
            "date": date,
            "strategy": strategy,
            "strategy_raw": strategy_raw,
            "selector_name": selector_name,
            "current_stock": current_stock,
            "selected_stocks": selected_stocks,
            "decision_raw": decision_raw,
            "input_data": input_data,
            "error": error,
        }

    def apply_investment_result(self, result: dict[str, Any], update_history: bool = True) -> None:
        self.strategy = result.get("strategy")
        selector_name = result.get("selector_name", "RandomStockSelector")
        self.stock_selector = self._build_selector(selector_name)
        current_stock = result.get("current_stock", [])
        selected_stocks = result.get("selected_stocks", [])
        input_data = result.get("input_data", "")
        if update_history:
            self.investing_history.add_records(input_data, current_stock, selected_stocks)
        if result.get("status") != "success":
            return
        selected_stock_res = {}
        for stock in current_stock:
            selected_stock_res[stock] = 1 if stock in selected_stocks else 0
        self.investment_analyzer.record_score(result["date"], self.modality, 1, selected_stock_res)
   
    def invest(self, date: int, num_stocks: int) -> None:
        result = self.run_investment_task(date, num_stocks)
        self.apply_investment_result(result)
