import json
import pickle
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class AgentTaskRecord:
    date: int
    agent_id: str
    status: str
    modality: int
    current_stock_json: str | None
    strategy_json: str | None
    strategy_raw: str | None
    selector_name: str | None
    selected_stocks_json: str | None
    decision_raw: str | None
    error: str | None


class CheckpointStore:
    def __init__(self, root_dir: str | Path, run_id: str, config: dict[str, Any], enabled: bool = True):
        self.enabled = enabled
        self.root_dir = Path(root_dir)
        self.run_dir = self.root_dir / run_id
        self.signals_dir = self.run_dir / "date_signals"
        self.optimizer_dir = self.run_dir / "date_optimizer"
        self.snapshots_dir = self.run_dir / "snapshots"
        self.agent_state_dir = self.run_dir / "agent_state"
        self.manifest_path = self.run_dir / "manifest.json"
        self.progress_path = self.run_dir / "progress.json"
        self.db_path = self.run_dir / "agent_results.sqlite"
        if not self.enabled:
            return
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.signals_dir.mkdir(exist_ok=True)
        self.optimizer_dir.mkdir(exist_ok=True)
        self.snapshots_dir.mkdir(exist_ok=True)
        self.agent_state_dir.mkdir(exist_ok=True)
        self._init_db()
        self._write_json_if_missing(self.manifest_path, config)
        self._write_json_if_missing(
            self.progress_path,
            {
                "last_committed_date": None,
                "completed_dates": [],
                "current_phase": "initialized",
                "current_date": None,
            },
        )

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_results (
                    date INTEGER NOT NULL,
                    agent_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    modality INTEGER NOT NULL,
                    current_stock_json TEXT,
                    strategy_json TEXT,
                    strategy_raw TEXT,
                    selector_name TEXT,
                    selected_stocks_json TEXT,
                    decision_raw TEXT,
                    error TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (date, agent_id)
                )
                """
            )

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _write_json_if_missing(self, path: Path, payload: dict[str, Any]) -> None:
        if path.exists():
            return
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="ascii")

    def load_progress(self) -> dict[str, Any]:
        if not self.enabled:
            return {
                "last_committed_date": None,
                "completed_dates": [],
                "current_phase": "disabled",
                "current_date": None,
            }
        return json.loads(self.progress_path.read_text(encoding="ascii"))

    def save_progress(self, **updates: Any) -> None:
        if not self.enabled:
            return
        progress = self.load_progress()
        progress.update(updates)
        self.progress_path.write_text(json.dumps(progress, indent=2, sort_keys=True), encoding="ascii")

    def load_cached_agent_result(self, date: int, agent_id: str) -> AgentTaskRecord | None:
        if not self.enabled:
            return None
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT date, agent_id, status, modality, current_stock_json, strategy_json,
                       strategy_raw, selector_name, selected_stocks_json, decision_raw, error
                FROM agent_results
                WHERE date = ? AND agent_id = ?
                """,
                (date, agent_id),
            ).fetchone()
        if row is None:
            return None
        return AgentTaskRecord(*row)

    def save_agent_result(self, record: AgentTaskRecord) -> None:
        if not self.enabled:
            return
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_results (
                    date, agent_id, status, modality, current_stock_json, strategy_json,
                    strategy_raw, selector_name, selected_stocks_json, decision_raw, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date, agent_id) DO UPDATE SET
                    status = excluded.status,
                    modality = excluded.modality,
                    current_stock_json = excluded.current_stock_json,
                    strategy_json = excluded.strategy_json,
                    strategy_raw = excluded.strategy_raw,
                    selector_name = excluded.selector_name,
                    selected_stocks_json = excluded.selected_stocks_json,
                    decision_raw = excluded.decision_raw,
                    error = excluded.error,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    record.date,
                    record.agent_id,
                    record.status,
                    record.modality,
                    record.current_stock_json,
                    record.strategy_json,
                    record.strategy_raw,
                    record.selector_name,
                    record.selected_stocks_json,
                    record.decision_raw,
                    record.error,
                ),
            )

    def save_date_signal(self, date: int, signal_df: pd.DataFrame) -> None:
        if not self.enabled:
            return
        path = self.signals_dir / f"{date}.parq"
        signal_df.to_parquet(path)

    def load_date_signals(self) -> dict[int, pd.DataFrame]:
        if not self.enabled:
            return {}
        results = {}
        for path in sorted(self.signals_dir.glob("*.parq")):
            results[int(path.stem)] = pd.read_parquet(path)
        return results

    def save_optimizer_state(self, date: int, payload: dict[str, Any]) -> None:
        if not self.enabled:
            return
        path = self.optimizer_dir / f"{date}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="ascii")

    def load_latest_optimizer_state(self) -> tuple[int | None, dict[str, Any] | None]:
        if not self.enabled:
            return None, None
        paths = sorted(self.optimizer_dir.glob("*.json"))
        if not paths:
            return None, None
        latest = paths[-1]
        return int(latest.stem), json.loads(latest.read_text(encoding="ascii"))

    def save_analyzer_snapshot(self, date: int, analyzer_state: dict[str, Any]) -> None:
        if not self.enabled:
            return
        path = self.snapshots_dir / f"analyzer_{date}.pkl"
        with path.open("wb") as fh:
            pickle.dump(analyzer_state, fh)

    def load_latest_analyzer_snapshot(self) -> tuple[int | None, dict[str, Any] | None]:
        if not self.enabled:
            return None, None
        paths = sorted(self.snapshots_dir.glob("analyzer_*.pkl"))
        if not paths:
            return None, None
        latest = paths[-1]
        with latest.open("rb") as fh:
            return int(latest.stem.split("_", 1)[1]), pickle.load(fh)

    def save_agent_state_snapshot(self, date: int, agent_states: dict[str, Any]) -> None:
        if not self.enabled:
            return
        path = self.agent_state_dir / f"agent_state_{date}.pkl"
        with path.open("wb") as fh:
            pickle.dump(agent_states, fh)

    def load_latest_agent_state_snapshot(self) -> tuple[int | None, dict[str, Any] | None]:
        if not self.enabled:
            return None, None
        paths = sorted(self.agent_state_dir.glob("agent_state_*.pkl"))
        if not paths:
            return None, None
        latest = paths[-1]
        with latest.open("rb") as fh:
            return int(latest.stem.split("_", 2)[2]), pickle.load(fh)
