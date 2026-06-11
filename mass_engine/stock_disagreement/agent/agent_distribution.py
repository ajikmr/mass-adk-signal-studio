import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from stock_disagreement.agent import InvestmentAnalyzer
import bisect
import concurrent
import random
from tqdm import tqdm
import time

class BaseOptimizer(ABC):
    """
    Base class for agent distribution optimization logic.
    """
    interval: int = 4
    def __init__(self,
                max_iter:int = 20,
                look_back_window: int = 5,
                fitness_signal_col: str = "Signal_std",
                turnover_penalty: float = 0.0,
                seed: int = 42):
        super().__init__()
        self.max_iter = max_iter
        self.look_back_window = look_back_window
        self.fitness_signal_col = fitness_signal_col
        self.turnover_penalty = turnover_penalty
        self.seed = seed
    

    def calcluate_fitness(self, investment_res: pd.DataFrame, stock_labels: pd.DataFrame, alpha: float = 0.5) -> float:
        sub_res = investment_res.copy()
        sub_res = investment_res.merge(stock_labels, on = ["Stock", "Date"], how="inner")
        label_col = "5_15_labelB"
        signal_col = self.fitness_signal_col
        rankic_values = sub_res.groupby(by = ["Date"])[["Stock",label_col, signal_col]].apply(
            lambda x: np.corrcoef(x[label_col].rank(), x[signal_col].rank())[0, 1]
        )

        return rankic_values.mean()

    def _calc_turnover(self, dist_a: dict[int, float], dist_b: dict[int, float]) -> float:
        """L1 turnover between two distributions: sum(|a_k - b_k|) / 2"""
        keys = set(dist_a.keys()) | set(dist_b.keys())
        return sum(abs(dist_a.get(k, 0.0) - dist_b.get(k, 0.0)) for k in keys) / 2

    @abstractmethod
    def optimize(self,
                investment_res: InvestmentAnalyzer,
                dates: list[int],
                current_date: int,
                stock_pool: pd.DataFrame,
                distribution: list[float]) -> list[float]:
        pass



class SimulatedAnnealingOptimizer(BaseOptimizer):
    """
    Simulated annealing optimizer.
    """
    mean: float = 0
    std_dev: float = 0.25
    def __init__(self,
                 look_back_window: int = 5,
                 max_iter:int = 20,
                 init_temp: float = 0.5,
                 cooling_rate: float = 0.95,
                 fitness_signal_col: str = "Signal_std",
                 turnover_penalty: float = 0.0,
                 seed: int = 42,
                  ):
        super().__init__(max_iter, look_back_window, fitness_signal_col, turnover_penalty, seed)
        self.init_temp = init_temp
        self.cooling_rate = cooling_rate
    
    def is_adjusted(self, dates:list[int], current_date: int) -> int:
        dates = sorted(dates)
        target_index = bisect.bisect_left(dates, current_date)
        if target_index - self.look_back_window - self.interval < 0:
            return -1
        return dates[target_index - self.look_back_window - self.interval]
    

    def _random_tweak(self, distribution: dict[int, float]) -> dict[float, int]:
        while True:
            sample = np.random.normal(self.mean, self.std_dev)
            keys = list(distribution.keys())
            if len(keys) < 2:
                raise ValueError("Agent type < 2!")
            selected_keys = random.sample(keys, 2)
            if distribution[selected_keys[0]] - sample <= 0 or distribution[selected_keys[1]] + sample <= 0:
                continue
            distribution[selected_keys[0]] -= sample
            distribution[selected_keys[1]] += sample
            return distribution
            

    def optimize(self, 
                investment_analyzer: InvestmentAnalyzer,
                dates: list[int],
                start_date: int,
                current_date:int,
                stock_labels: pd.DataFrame,
                stock_pool:pd.DataFrame, 
                distribution: dict[int, float]
                ) -> dict[int, float]:
        dates = sorted(dates)
        current_temp = self.init_temp
        start_index = bisect.bisect_left(dates, start_date)
        search_dates = dates[start_index: start_index + self.look_back_window].copy()
        end_date = search_dates[-1]
        cuurent_distribution = distribution.copy()
        initial_distribution = distribution.copy()
        investment_res = self.get_investment_res(investment_analyzer, start_date, current_date, stock_pool, end_date, cuurent_distribution, search_dates)
        current_fitness = self.calcluate_fitness(investment_res=investment_res, stock_labels=stock_labels)
        if self.turnover_penalty > 0:
            current_fitness -= self.turnover_penalty * self._calc_turnover(cuurent_distribution, initial_distribution)
        best_distributions = distribution.copy()
        best_fitness = current_fitness
        for i in tqdm(range(self.max_iter), desc=f"optimizing {current_date}"):

            tweaked_distribution = self._random_tweak(cuurent_distribution.copy())
            fitness = self.calcluate_fitness(investment_res=self.get_investment_res(investment_analyzer, start_date, current_date, stock_pool, end_date, tweaked_distribution, search_dates),
                                              stock_labels=stock_labels)
            if self.turnover_penalty > 0:
                fitness -= self.turnover_penalty * self._calc_turnover(tweaked_distribution, initial_distribution)
            if fitness > current_fitness:
                cuurent_distribution = tweaked_distribution
                current_fitness = fitness
            else:
                diff = (current_fitness - fitness) * 10  
                prob = np.exp(-diff / current_temp)  
                if random.random() < prob:  
                    cuurent_distribution = tweaked_distribution
                    current_fitness = fitness
            if current_fitness > best_fitness:
                best_fitness = current_fitness
                best_distributions = cuurent_distribution
            current_temp *= self.cooling_rate

        return best_distributions


    def get_investment_res(self, investment_analyzer:InvestmentAnalyzer, start_date:int, current_date:int, stock_pool:pd.DataFrame, end_date:int,
                           agent_distributions: dict[int, float], dates: list[int]):
        investment_res = stock_pool[(stock_pool["Date"] >= start_date) & (stock_pool["Date"] <= end_date)].copy()
        def _calc_signal(date: int): 
            current_pool = stock_pool[stock_pool["Date"] == date]["Stock"].tolist()  
            res = investment_analyzer.calculate_stock_disagreement_score(date=date, stock_pool=current_pool, agent_distributions=agent_distributions)  
            return date, res   
        
        date_signal_results = {}  
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:  
            date_futures = {executor.submit(_calc_signal, date): date for date in dates}  
            for future in tqdm(  
                concurrent.futures.as_completed(date_futures),  
                total=len(dates),  
                desc=f"Calculating signals {start_date} ~ {end_date}, while current date is {current_date}"  
                ):  
                date, result = future.result()  
                date_signal_results[date] = result 
        
        data_list = []
        for date, res in date_signal_results.items():
            for stock, values in res.items():
                data_list.append([date, stock, values[0], values[1], values[2]])
        result_df = pd.DataFrame(data_list, columns=['Date', 'Stock', 'Signal', 'Signal_mean', 'Signal_std'])
        investment_res = pd.merge(investment_res, result_df, on=['Date', 'Stock'], how='left')
        investment_res[['Signal', 'Signal_mean', 'Signal_std']] = investment_res[['Signal', 'Signal_mean', 'Signal_std']].fillna(0)
        return investment_res


class CMAESOptimizer(BaseOptimizer):
    """
    CMA-ES optimizer for agent distribution optimization.
    Models full covariance between distribution weights for more efficient search.
    """
    def __init__(self,
                 look_back_window: int = 5,
                 max_iter: int = 15,
                 sigma0: float = 0.2,
                 fitness_signal_col: str = "Signal_std",
                 learn_alpha: bool = False,
                 alpha_init: float = 0.5,
                 turnover_penalty: float = 0.0,
                 seed: int = 42,
                  ):
        super().__init__(max_iter, look_back_window, fitness_signal_col, turnover_penalty, seed)
        self.sigma0 = sigma0
        self.learn_alpha = learn_alpha
        self.alpha_init = alpha_init
        self.best_alpha = alpha_init

    def is_adjusted(self, dates: list[int], current_date: int) -> int:
        dates = sorted(dates)
        target_index = bisect.bisect_left(dates, current_date)
        if target_index - self.look_back_window - self.interval < 0:
            return -1
        return dates[target_index - self.look_back_window - self.interval]

    def _dict_to_vec(self, distribution: dict[int, float]) -> tuple[list[float], list[int]]:
        keys = sorted(distribution.keys())
        vec = [distribution[k] for k in keys]
        return vec, keys

    def _vec_to_dict(self, vec: list[float], keys: list[int]) -> dict[int, float]:
        return {k: max(v, 1e-6) for k, v in zip(keys, vec)}

    def optimize(self,
                investment_analyzer: InvestmentAnalyzer,
                dates: list[int],
                start_date: int,
                current_date: int,
                stock_labels: pd.DataFrame,
                stock_pool: pd.DataFrame,
                distribution: dict[int, float],
                ) -> dict[int, float]:
        import cma

        dates = sorted(dates)
        start_index = bisect.bisect_left(dates, start_date)
        search_dates = dates[start_index: start_index + self.look_back_window].copy()
        end_date = search_dates[-1]

        vec, keys = self._dict_to_vec(distribution)
        initial_distribution = distribution.copy()

        # If learn_alpha, append alpha to the search vector
        if self.learn_alpha:
            x0 = vec + [self.alpha_init]
        else:
            x0 = vec

        def _objective(x):
            if self.learn_alpha:
                dist_vec = x[:-1]
                alpha_val = float(np.clip(x[-1], 0.0, 1.0))
            else:
                dist_vec = x
                alpha_val = 0.5  # not used when learn_alpha=False

            dist_dict = self._vec_to_dict(dist_vec, keys)
            investment_res = self.get_investment_res(
                investment_analyzer, start_date, current_date, stock_pool,
                end_date, dist_dict, search_dates, alpha=alpha_val
            )
            fitness = self.calcluate_fitness(investment_res=investment_res, stock_labels=stock_labels)
            if self.turnover_penalty > 0:
                fitness -= self.turnover_penalty * self._calc_turnover(dist_dict, initial_distribution)
            return -fitness  # CMA-ES minimizes

        # Set up bounds: weights >= 0, alpha in [0, 1] if learn_alpha
        lower_bounds = [1e-6] * len(vec)
        upper_bounds = [None] * len(vec)
        if self.learn_alpha:
            lower_bounds.append(0.0)
            upper_bounds.append(1.0)

        opts = {
            'bounds': [lower_bounds, upper_bounds],
            'maxfevals': self.max_iter * 2,
            'verbose': -1,
            'seed': self.seed,
        }

        es = cma.CMAEvolutionStrategy(x0, self.sigma0, opts)
        es.optimize(_objective)

        best_x = es.result.xbest
        if self.learn_alpha:
            best_dist_vec = best_x[:-1]
            self.best_alpha = float(np.clip(best_x[-1], 0.0, 1.0))
        else:
            best_dist_vec = best_x

        best_distribution = self._vec_to_dict(best_dist_vec, keys)
        return best_distribution

    def get_investment_res(self, investment_analyzer: InvestmentAnalyzer, start_date: int, current_date: int,
                           stock_pool: pd.DataFrame, end_date: int,
                           agent_distributions: dict[int, float], dates: list[int],
                           alpha: float = 0.5):
        investment_res = stock_pool[(stock_pool["Date"] >= start_date) & (stock_pool["Date"] <= end_date)].copy()

        def _calc_signal(date: int):
            current_pool = stock_pool[stock_pool["Date"] == date]["Stock"].tolist()
            res = investment_analyzer.calculate_stock_disagreement_score(
                date=date, stock_pool=current_pool,
                agent_distributions=agent_distributions, alpha=alpha
            )
            return date, res

        date_signal_results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            date_futures = {executor.submit(_calc_signal, date): date for date in dates}
            for future in tqdm(
                concurrent.futures.as_completed(date_futures),
                total=len(dates),
                desc=f"CMA-ES signals {start_date} ~ {end_date}, alpha={alpha:.3f}"
            ):
                date, result = future.result()
                date_signal_results[date] = result

        data_list = []
        for date, res in date_signal_results.items():
            for stock, values in res.items():
                data_list.append([date, stock, values[0], values[1], values[2]])
        result_df = pd.DataFrame(data_list, columns=['Date', 'Stock', 'Signal', 'Signal_mean', 'Signal_std'])
        investment_res = pd.merge(investment_res, result_df, on=['Date', 'Stock'], how='left')
        investment_res[['Signal', 'Signal_mean', 'Signal_std']] = investment_res[['Signal', 'Signal_mean', 'Signal_std']].fillna(0)
        return investment_res

        


        
