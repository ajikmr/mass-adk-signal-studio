import concurrent.futures
import json
import random
from typing import Any, List

import numpy as np
import pandas as pd
from scipy.stats import percentileofscore
from tqdm import tqdm

from stock_disagreement import Modality, StockDisagreementAgent
from stock_disagreement import InvestmentAnalyzer, SimulatedAnnealingOptimizer, CMAESOptimizer
from stock_disagreement.exp.checkpoint import AgentTaskRecord, CheckpointStore


class StockDisagreementTrainer:
    def __init__(self,
                 num_investor_type: int,
                 num_agents_per_investor: int,
                 stock_selector_for_per_investor: int,
                 stock_pool_name: str,
                 dataset_dir: str,
                 stock_pool: pd.DataFrame,
                 stock_labels: pd.DataFrame,
                 stock_num: int,
                 look_back_window: int,
                 start_date: int | None = None,
                 end_date: int | None = None,
                 use_prev_stock: bool = False,
                 use_self_reflection: bool = False,
                 use_macro_data: bool = False,
                 use_agent_distribution_modification: bool = False,
                 optimizer_look_back_window: int = 2,
                 data_leakage: bool = False,
                 optimizer_type: str = "sa",
                 fitness_signal_col: str = "Signal_std",
                 learn_alpha: bool = False,
                 turnover_penalty: float = 0.0,
                 checkpoint_store: CheckpointStore | None = None,
                 max_agent_workers: int = 32,
                 request_timeout: float = 120.0,
                 seed: int = 42,
                 dotenv_path: str | None = None,
                  ): 
        self.interval = 4
        self.num_investor_type = num_investor_type
        self.stock_selector_for_per_investor = stock_selector_for_per_investor
        self.stock_pool_name = stock_pool_name
        self.dataset_dir = dataset_dir
        self.num_agents_per_investor = num_agents_per_investor
        self.stock_num = stock_num
        self.stock_pool = stock_pool
        self.stock_labels = stock_labels
        self.look_back_window = look_back_window
        self.stock_labels = self.stock_labels.merge(self.stock_pool[["Stock", "Date"]], on=["Stock", "Date"])
        self.optimizer_look_back_window = optimizer_look_back_window
        self.use_agent_distribution_modification = use_agent_distribution_modification
        self.use_prev_stock = use_prev_stock
        self.use_self_reflection = use_self_reflection
        self.use_macro_data = use_macro_data
        self.data_leakage = data_leakage
        self.learn_alpha = learn_alpha
        self.request_timeout = request_timeout
        self.max_agent_workers = max_agent_workers
        self.seed = seed
        self.dotenv_path = dotenv_path
        self.checkpoint_store = checkpoint_store
        self.agent_distributions: dict[int, float] = {}
        self.date_agent_distributions: dict[int, Any] = {}

        if start_date is not None:
            self.start_date = start_date
        else:
            self.start_date = stock_pool["Date"].min()
        if end_date is not None:
            self.end_date = end_date
        else:
            self.end_date = stock_pool["Date"].max()

        self.stock_pool = self.stock_pool[(self.stock_pool["Date"] >= self.start_date) & (self.stock_pool["Date"] <= self.end_date)]
        self.stock_labels = self.stock_labels[(self.stock_labels["Date"] >= self.start_date) & (self.stock_labels["Date"] <= self.end_date)]
        self.dates = sorted(self.stock_pool[(self.stock_pool["Date"] >= self.start_date) & (self.stock_pool["Date"] <= self.end_date)]["Date"].unique().tolist())
        self.completed_signal_dates: set[int] = set()

        self.news_info = pd.read_parquet(f"{self.dataset_dir}/wind-financial-news-info.parq")
        self.news_relationship = pd.read_parquet(f"{self.dataset_dir}/wind-financial-news-relationship.parq")
        self.news_info["Date"] = self.news_info["Date"].astype("int32")
        self.news_relationship["Date"] = self.news_relationship["Date"].astype("int32")

        self.investment_analyzer = InvestmentAnalyzer()
        self.investment_analyzer.reset()
        self.agents: List[StockDisagreementAgent] = []
        self._init_agents()

        if optimizer_type == "cma_es":
            self.optimzer = CMAESOptimizer(
                look_back_window=optimizer_look_back_window,
                fitness_signal_col=fitness_signal_col,
                learn_alpha=learn_alpha,
                turnover_penalty=turnover_penalty,
                seed=seed,
            )
        else:
            self.optimzer = SimulatedAnnealingOptimizer(
                look_back_window=optimizer_look_back_window,
                fitness_signal_col=fitness_signal_col,
                turnover_penalty=turnover_penalty,
                seed=seed,
            )

        self._restore_from_checkpoint()

    def _init_agents(self) -> None:
        def cal_pe_quantile(data: pd.DataFrame, look_back_year: int = 10) -> pd.DataFrame:
            data_copy = data.copy()
            data_copy["dt"] = pd.to_datetime(data_copy["Date"].astype(str), format="%Y%m%d")
            data_copy.sort_values("dt", inplace=True)
            data_copy.reset_index(drop=True, inplace=True)
            min_periods = look_back_year * 250
            data_copy["quantile"] = data_copy["Value"].rolling(window=min_periods, closed="both").apply(
                lambda x: percentileofscore(x, x.iloc[-1]), raw=False
            )
            data_copy["quantile"] = data_copy["quantile"].round(1)
            data_copy["Date"] = data_copy["dt"].dt.strftime("%Y%m%d").astype(int)
            return data_copy[["Date", "Value", "quantile"]]

        macro_dir = f"{self.dataset_dir}/macro_data"
        loan_rate = pd.read_csv(f"{macro_dir}/policy_rate.csv")
        cpi = pd.read_csv(f"{macro_dir}/cpi_yoy.csv")
        csi_300_pe = pd.read_csv(f"{macro_dir}/equity_index_pe_ttm.csv")
        market_sentiment_index = pd.read_csv(f"{macro_dir}/market_sentiment.csv")
        yield_on_China_bonds = pd.read_csv(f"{macro_dir}/ten_year_government_bond_yield.csv")
        csi_300_pe = cal_pe_quantile(csi_300_pe)

        for type_idx in tqdm(range(self.num_investor_type), desc="Init agents"):
            available_modalities = [Modality.BASE_DATA, Modality.CROSS_INDUSTRY_LABEL, Modality.PRICE_FEATURE]
            selected_modalities = random.sample(available_modalities, k=random.randint(1, min(3, len(available_modalities))))
            result = Modality(0)
            for modality in selected_modalities:
                result |= modality
            self.agent_distributions[int(result)] = 1.0
            for agent_idx in range(self.num_agents_per_investor):
                current_agent = StockDisagreementAgent(
                    stock_num=self.stock_num,
                    stock_pool=self.stock_pool,
                    stock_labels=self.stock_labels,
                    is_self_reflective=True,
                    max_reflective_times=10,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    modality=result,
                    use_prev_stock=self.use_prev_stock,
                    cpi=cpi,
                    csi_300_pe=csi_300_pe,
                    loan_rate=loan_rate,
                    market_sentiment_index=market_sentiment_index,
                    yield_on_China_bonds=yield_on_China_bonds,
                    use_self_reflection=self.use_self_reflection,
                    use_macro_data=self.use_macro_data,
                    dataset_dir=self.dataset_dir,
                    stock_pool_name=self.stock_pool_name,
                    request_timeout=self.request_timeout,
                    dotenv_path=self.dotenv_path,
                    agent_id=f"type{type_idx}_agent{agent_idx}_mod{int(result)}",
                )
                current_agent.prepare_data_source(self.news_info, self.news_relationship)
                self.agents.append(current_agent)

    def _restore_from_checkpoint(self) -> None:
        if self.checkpoint_store is None or not self.checkpoint_store.enabled:
            return

        snapshot_date, analyzer_state = self.checkpoint_store.load_latest_analyzer_snapshot()
        if analyzer_state is not None:
            self.investment_analyzer.load_state(analyzer_state)

        agent_state_date, agent_states = self.checkpoint_store.load_latest_agent_state_snapshot()
        if agent_states:
            for agent in self.agents:
                agent.load_runtime_state(agent_states.get(agent.agent_id))

        optimizer_date, optimizer_state = self.checkpoint_store.load_latest_optimizer_state()
        if optimizer_state is not None:
            self.agent_distributions = {int(k): v for k, v in optimizer_state.get("agent_distributions", {}).items()}
            self.date_agent_distributions = {int(k): {int(inner_k): inner_v for inner_k, inner_v in value.items()} for k, value in optimizer_state.get("date_agent_distributions", {}).items()}
            if self.learn_alpha and hasattr(self.optimzer, "best_alpha"):
                self.optimzer.best_alpha = optimizer_state.get("best_alpha", self.optimzer.best_alpha)

        if snapshot_date is None:
            snapshot_date = optimizer_date
        if snapshot_date is None:
            snapshot_date = agent_state_date

        progress = self.checkpoint_store.load_progress()
        self.completed_signal_dates = set(progress.get("completed_dates", []))

        if snapshot_date is None:
            return

        for date in self.dates:
            if date <= snapshot_date:
                continue
            if date not in self.completed_signal_dates:
                break
            for agent in self.agents:
                cached = self.checkpoint_store.load_cached_agent_result(date, agent.agent_id)
                if cached is None or cached.status != "success":
                    continue
                result = {
                    "status": cached.status,
                    "date": cached.date,
                    "agent_id": cached.agent_id,
                    "modality": cached.modality,
                    "current_stock": json.loads(cached.current_stock_json or "[]"),
                    "strategy": json.loads(cached.strategy_json or "{}"),
                    "strategy_raw": cached.strategy_raw,
                    "selector_name": cached.selector_name,
                    "selected_stocks": json.loads(cached.selected_stocks_json or "[]"),
                    "decision_raw": cached.decision_raw,
                    "input_data": "",
                    "error": cached.error,
                }
                agent.apply_investment_result(result, update_history=False)

    def _serialize_agent_result(self, result: dict[str, Any]) -> AgentTaskRecord:
        return AgentTaskRecord(
            date=result["date"],
            agent_id=result["agent_id"],
            status=result["status"],
            modality=int(result["modality"]),
            current_stock_json=json.dumps(result.get("current_stock", [])),
            strategy_json=json.dumps(result.get("strategy", {})),
            strategy_raw=result.get("strategy_raw"),
            selector_name=result.get("selector_name"),
            selected_stocks_json=json.dumps(result.get("selected_stocks", [])),
            decision_raw=result.get("decision_raw"),
            error=result.get("error"),
        )

    def _load_cached_result_payload(self, record: AgentTaskRecord) -> dict[str, Any]:
        return {
            "status": record.status,
            "date": record.date,
            "agent_id": record.agent_id,
            "modality": record.modality,
            "current_stock": json.loads(record.current_stock_json or "[]"),
            "strategy": json.loads(record.strategy_json or "{}"),
            "strategy_raw": record.strategy_raw,
            "selector_name": record.selector_name,
            "selected_stocks": json.loads(record.selected_stocks_json or "[]"),
            "decision_raw": record.decision_raw,
            "input_data": "",
            "error": record.error,
        }

    def _process_date(self, date: int) -> None:
        if self.checkpoint_store is not None:
            self.checkpoint_store.save_progress(current_phase="processing_agents", current_date=date)

        task_results: list[dict[str, Any]] = []
        pending_agents: list[StockDisagreementAgent] = []
        for agent in self.agents:
            cached = None if self.checkpoint_store is None else self.checkpoint_store.load_cached_agent_result(date, agent.agent_id)
            if cached is not None and cached.status == "success":
                task_results.append(self._load_cached_result_payload(cached))
            else:
                pending_agents.append(agent)

        if pending_agents:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_agent_workers) as executor:
                future_map = {
                    executor.submit(agent.run_investment_task, date, self.stock_selector_for_per_investor): agent
                    for agent in pending_agents
                }
                for future in tqdm(concurrent.futures.as_completed(future_map), total=len(future_map), desc=f"Processing agent on {date}"):
                    result = future.result()
                    task_results.append(result)
                    if self.checkpoint_store is not None:
                        self.checkpoint_store.save_agent_result(self._serialize_agent_result(result))

        task_results.sort(key=lambda item: item["agent_id"])
        agent_lookup = {agent.agent_id: agent for agent in self.agents}
        for result in task_results:
            agent_lookup[result["agent_id"]].apply_investment_result(result)

        res = self.optimzer.is_adjusted(self.dates, date)
        if res > 0:
            self.date_agent_distributions[date] = self.agent_distributions.copy()
            best_distributions = self.optimzer.optimize(
                investment_analyzer=self.investment_analyzer,
                dates=self.dates,
                start_date=res,
                current_date=date,
                stock_labels=self.stock_labels,
                stock_pool=self.stock_pool,
                distribution=self.agent_distributions,
            )
            self.agent_distributions = best_distributions
            if self.data_leakage:
                self.date_agent_distributions[date] = best_distributions
        else:
            self.date_agent_distributions[date] = self.agent_distributions.copy()

        current_alpha = 0.5
        if self.learn_alpha and hasattr(self.optimzer, "best_alpha"):
            current_alpha = self.optimzer.best_alpha
        current_pool = self.stock_pool[self.stock_pool["Date"] == date]["Stock"].tolist()
        signal_result = self.investment_analyzer.calculate_stock_disagreement_score(
            date,
            current_pool,
            agent_distributions=self.date_agent_distributions[date] if self.use_agent_distribution_modification else self.agent_distributions,
            alpha=current_alpha,
        )
        signal_rows = [[date, stock, values[0], values[1], values[2]] for stock, values in signal_result.items()]
        signal_df = pd.DataFrame(signal_rows, columns=["Date", "Stock", "Signal", "Signal_mean", "Signal_std"])

        if self.checkpoint_store is not None:
            self.checkpoint_store.save_date_signal(date, signal_df)
            self.checkpoint_store.save_optimizer_state(
                date,
                {
                    "agent_distributions": self.agent_distributions,
                    "date_agent_distributions": self.date_agent_distributions,
                    "best_alpha": getattr(self.optimzer, "best_alpha", 0.5),
                },
            )
            self.checkpoint_store.save_analyzer_snapshot(date, self.investment_analyzer.export_state())
            self.checkpoint_store.save_agent_state_snapshot(
                date,
                {agent.agent_id: agent.export_runtime_state() for agent in self.agents},
            )
            completed_dates = sorted(self.completed_signal_dates | {date})
            self.completed_signal_dates = set(completed_dates)
            self.checkpoint_store.save_progress(
                current_phase="date_committed",
                current_date=date,
                last_committed_date=date,
                completed_dates=completed_dates,
            )
        else:
            self.completed_signal_dates.add(date)

    def run(self) -> pd.DataFrame:
        pending_dates = [date for date in self.dates if date not in self.completed_signal_dates]
        for date in pending_dates:
            self._process_date(date)

        date_signal_frames = {}
        if self.checkpoint_store is not None:
            date_signal_frames = self.checkpoint_store.load_date_signals()

        if not date_signal_frames:
            current_alpha = 0.5
            if self.learn_alpha and hasattr(self.optimzer, "best_alpha"):
                current_alpha = self.optimzer.best_alpha
            for date in self.dates:
                current_pool = self.stock_pool[self.stock_pool["Date"] == date]["Stock"].tolist()
                signal_result = self.investment_analyzer.calculate_stock_disagreement_score(
                    date,
                    current_pool,
                    agent_distributions=self.date_agent_distributions.get(date, self.agent_distributions),
                    alpha=current_alpha,
                )
                signal_rows = [[date, stock, values[0], values[1], values[2]] for stock, values in signal_result.items()]
                date_signal_frames[date] = pd.DataFrame(signal_rows, columns=["Date", "Stock", "Signal", "Signal_mean", "Signal_std"])

        if date_signal_frames:
            result_df = pd.concat(date_signal_frames.values(), ignore_index=True)
        else:
            result_df = pd.DataFrame(columns=["Date", "Stock", "Signal", "Signal_mean", "Signal_std"])

        investment_res = self.stock_pool[(self.stock_pool["Date"] >= self.start_date) & (self.stock_pool["Date"] <= self.end_date)].copy()
        investment_res = pd.merge(investment_res, result_df, on=["Date", "Stock"], how="left")
        return investment_res
