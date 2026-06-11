import argparse
import os
import pickle as pkl
from pathlib import Path
import random

import numpy as np
import pandas as pd

from stock_disagreement import CheckpointStore, StockDisagreementTrainer

ENGINE_ROOT = Path(__file__).resolve().parents[1]
MASS_ADK_ROOT = ENGINE_ROOT.parent
DEFAULT_DATASET_ROOT = MASS_ADK_ROOT / "sample_data" / "ih_smoke"
DEFAULT_SP500_DATASET_ROOT = MASS_ADK_ROOT / "sample_data" / "sp500_smoke"
DEFAULT_RESULT_ROOT = MASS_ADK_ROOT / "artifacts" / "mass_engine" / "results"

def calculate_ic_rankic(res: pd.DataFrame, stock_labels: pd.DataFrame):
  
    label_cols = ["1_15_labelB", "5_15_labelB", "10_15_labelB"]
    sub_res = res[res["Date"] >= 20230102]
    df = sub_res[["Stock", "Date", "Signal", "Signal_mean", "Signal_std"]].merge(stock_labels[["Stock", "Date"] + label_cols], on=["Stock", "Date"])
    for label_col in label_cols:
        temp_df = df[[label_col, "Signal", "Signal_mean", "Signal_std"] + ["Stock", "Date"]].copy()
      
        rankic_values = temp_df.groupby(by = ["Date"])[["Stock",label_col, "Signal"]].apply(
            lambda x: np.corrcoef(x[label_col].rank(), x["Signal"].rank())[0, 1]
        )
        ic_values = temp_df.groupby(by = ["Date"])[["Stock",label_col, "Signal"]].apply(
            lambda x: np.corrcoef(x[label_col], x["Signal"])[0, 1]
        )
        rankic_values_mean = temp_df.groupby(by = ["Date"])[["Stock",label_col, "Signal_mean"]].apply(
            lambda x: np.corrcoef(x[label_col].rank(), x["Signal_mean"].rank())[0, 1]
        )
        ic_values_mean = temp_df.groupby(by = ["Date"])[["Stock",label_col, "Signal_mean"]].apply(
            lambda x: np.corrcoef(x[label_col], x["Signal_mean"])[0, 1]
        )
        rankic_values_std = temp_df.groupby(by = ["Date"])[["Stock",label_col, "Signal_std"]].apply(
            lambda x: np.corrcoef(x[label_col].rank(), x["Signal_std"].rank())[0, 1]
        )
        ic_values_std = temp_df.groupby(by = ["Date"])[["Stock", label_col, "Signal_std"]].apply(
            lambda x: np.corrcoef(x[label_col], x["Signal_std"])[0, 1]
        )

        rankic_ir = rankic_values.mean() / rankic_values.std()
        rankic = rankic_values.mean()
        ic = ic_values.mean()
        icir = ic_values.mean() / ic_values.std()
        print(f"for {label_col}, ic: {ic}, icir: {icir}, rankic: {rankic}, rankicir: {rankic_ir}")
        print(f"for {label_col}, ic_mean: {ic_values_mean.mean()}, icir_mean: {ic_values_mean.mean() / ic_values_mean.std()}, rankic_mean: {rankic_values_mean.mean()}, rankicir_mean: {rankic_values_mean.mean() / rankic_values_mean.std()}")
        print(f"for {label_col}, ic_std: {ic_values_std.mean()}, icir_mean: {ic_values_std.mean() / ic_values_std.std()}, rankic_mean: {rankic_values_std.mean()}, rankicir_mean: {rankic_values_std.mean() / rankic_values_std.std()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Stock disagreement argument parser.")
    parser.add_argument("--num_investor_type", type=int, default= 16)
    parser.add_argument("--num_agents_per_investor", type=int, default= 32)
    parser.add_argument("--stock_pool", type=str, default="ih", choices=["ih", "csi_300", "csi_500", "csi_1000", "start_up_100", "sp500"])
    parser.add_argument("--stock_num", type=int, default=20)
    parser.add_argument("--selected_stock_num", type=int, default=5)
    parser.add_argument("--start_date", type=int, default= 20221202)
    parser.add_argument("--end_date", type=int, default= 20240102)
    parser.add_argument("--use_prev_stock", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--use_self_reflection", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--use_macro_data", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--use_agent_distribution_modification", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--optimizer_look_back_window", type=int, default=5)
    parser.add_argument("--allow_possible_data_leakage", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--optimizer", type=str, default="sa", choices=["sa", "cma_es"])
    parser.add_argument("--fitness_signal_col", type=str, default="Signal_std", choices=["Signal_std", "Signal"])
    parser.add_argument("--learn_alpha", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--turnover_penalty", type=float, default=0.0)
    parser.add_argument("--max_agent_workers", type=int, default=32)
    parser.add_argument("--request_timeout", type=float, default=120.0)
    parser.add_argument("--dataset_root", type=str, default=os.getenv("MASS_ADK_DATASET_ROOT", str(DEFAULT_DATASET_ROOT)))
    parser.add_argument("--sp500_dataset_root", type=str, default=os.getenv("MASS_ADK_SP500_DATA_ROOT", os.getenv("MASS_ADK_SP500_DATASET_ROOT", str(DEFAULT_SP500_DATASET_ROOT))))
    parser.add_argument("--result_root", type=str, default=os.getenv("MASS_ADK_ENGINE_RESULT_ROOT", str(DEFAULT_RESULT_ROOT)))
    parser.add_argument("--checkpoint_root", type=str, default=None)
    parser.add_argument("--disable_checkpoint", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dotenv_path", type=str, default=os.getenv("MASS_ADK_DOTENV_PATH", str(MASS_ADK_ROOT / ".env")))

    args = parser.parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)

    stock_pool_name = args.stock_pool
    assert isinstance(stock_pool_name, str)
    result_root = Path(args.result_root)
    result_root.mkdir(parents=True, exist_ok=True)
    if args.checkpoint_root is None:
        args.checkpoint_root = str(result_root / "checkpoints")
    dataset_dir = args.sp500_dataset_root if stock_pool_name == "sp500" else args.dataset_root
    stock_pool = pd.read_parquet(f"{dataset_dir}/{stock_pool_name}.parq")
    industry = pd.read_parquet(f"{dataset_dir}/stock_basic_data.parq")
    stock_pool = stock_pool.merge(industry[["Stock", "Name", "Industry"]], on=["Stock"], how="left")
    # Change to your label file url here.
    stock_labels = pd.read_parquet(f"{dataset_dir}/all_ashare_label.parq")
    seed_suffix = f"seed{args.seed:02d}"
    run_suffix = f"{stock_pool_name}_{args.num_agents_per_investor}_{args.num_investor_type}_{args.use_macro_data}_{args.use_agent_distribution_modification}_{args.optimizer_look_back_window}_{args.allow_possible_data_leakage}_{args.start_date}_{args.end_date}_{args.use_self_reflection}_{args.optimizer}_{args.fitness_signal_col}_{args.learn_alpha}_{args.turnover_penalty}_{seed_suffix}_std"
    checkpoint_store = CheckpointStore(
        root_dir=args.checkpoint_root,
        run_id=run_suffix,
        config={
            "stock_pool": stock_pool_name,
            "dataset_dir": dataset_dir,
            "run_suffix": run_suffix,
            "args": vars(args),
        },
        enabled=not args.disable_checkpoint,
    )

    trainer = StockDisagreementTrainer(
        num_investor_type=args.num_investor_type,
        num_agents_per_investor=args.num_agents_per_investor,
        stock_selector_for_per_investor=args.selected_stock_num,
        stock_pool_name=stock_pool_name,
        dataset_dir=dataset_dir,
        stock_pool=stock_pool,
        stock_labels=stock_labels,
        stock_num = args.stock_num,
        start_date = args.start_date,
        end_date = args.end_date,
        use_prev_stock = args.use_prev_stock,
        use_self_reflection = args.use_self_reflection,
        use_macro_data = args.use_macro_data,
        use_agent_distribution_modification = args.use_agent_distribution_modification,
        look_back_window = 10,
        optimizer_look_back_window = args.optimizer_look_back_window,
        data_leakage = args.allow_possible_data_leakage,
        optimizer_type = args.optimizer,
        fitness_signal_col = args.fitness_signal_col,
        learn_alpha = args.learn_alpha,
        turnover_penalty = args.turnover_penalty,
        checkpoint_store = checkpoint_store,
        max_agent_workers = args.max_agent_workers,
        request_timeout = args.request_timeout,
        seed = args.seed,
        dotenv_path = args.dotenv_path,
    )
    res = trainer.run()
    res.to_parquet(result_root / f"{run_suffix}.parq")
    with open(result_root / f"dist_{run_suffix}_{args.stock_num}_positive.pkl", "wb") as f:
        pkl.dump(trainer.agent_distributions, f)
    calculate_ic_rankic(res, stock_labels)
