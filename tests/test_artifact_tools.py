import json
import sqlite3
from pathlib import Path

from mass_adk.tools import (
    inspect_mass_checkpoint,
    list_mass_checkpoints,
    list_mass_result_artifacts,
    validate_mass_runtime_paths,
)
from mass_adk.tools.manifest import load_manifest


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _create_sqlite(path: Path):
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE agent_results (date INTEGER, agent_id INTEGER)")
        connection.executemany(
            "INSERT INTO agent_results VALUES (?, ?)",
            [(20230615, 64), (20230615, 256)],
        )


def test_validate_mass_runtime_paths_reports_configured_roots(tmp_path, monkeypatch):
    results_root = tmp_path / "res"
    results_root.mkdir()
    monkeypatch.setenv("MASS_ADK_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("MASS_ADK_RESULTS_ROOT", str(results_root))

    result = validate_mass_runtime_paths()

    assert result["paths"]["mass_root"]["exists"] is True
    assert result["paths"]["results_root"]["exists"] is True
    assert result["configured_model"] == "gemini-3.5-flash"


def test_list_mass_result_artifacts_filters_stock_pool(tmp_path, monkeypatch):
    results_root = tmp_path / "res"
    results_root.mkdir()
    (results_root / "ih_smoke.parq").write_text("placeholder", encoding="utf-8")
    (results_root / "dist_ih_smoke.pkl").write_text("placeholder", encoding="utf-8")
    (results_root / "sp500_other.parq").write_text("placeholder", encoding="utf-8")
    monkeypatch.setenv("MASS_ADK_RESULTS_ROOT", str(results_root))

    result = list_mass_result_artifacts(stock_pool="ih")

    assert result["count"] == 2
    assert {artifact["kind"] for artifact in result["artifacts"]} == {
        "distribution",
        "signal_result",
    }


def test_inspect_mass_checkpoint_reads_progress_and_sqlite(tmp_path, monkeypatch):
    results_root = tmp_path / "res"
    run_id = "ih_smoke_run"
    run_path = results_root / "checkpoints" / run_id
    (run_path / "date_signals").mkdir(parents=True)
    (run_path / "date_optimizer").mkdir()
    (run_path / "agent_state").mkdir()
    (run_path / "snapshots").mkdir()
    (run_path / "date_signals" / "20230615.parq").write_text(
        "placeholder", encoding="utf-8"
    )
    (run_path / "date_optimizer" / "20230615.json").write_text(
        "{}", encoding="utf-8"
    )
    _write_json(run_path / "manifest.json", {"run_suffix": run_id, "stock_pool": "ih"})
    _write_json(
        run_path / "progress.json",
        {
            "completed_dates": [20230615],
            "current_phase": "date_committed",
            "last_committed_date": 20230615,
        },
    )
    _create_sqlite(run_path / "agent_results.sqlite")
    monkeypatch.setenv("MASS_ADK_RESULTS_ROOT", str(results_root))

    listed = list_mass_checkpoints(stock_pool="ih")
    inspected = inspect_mass_checkpoint(run_id)

    assert listed["count"] == 1
    assert listed["checkpoints"][0]["completed_date_count"] == 1
    assert inspected["progress"]["current_phase"] == "date_committed"
    assert inspected["artifact_counts"]["date_signal_parq"] == 1
    assert inspected["sqlite"]["tables"][0]["row_count"] == 2


def test_inspect_mass_checkpoint_rejects_path_traversal(tmp_path, monkeypatch):
    results_root = tmp_path / "res"
    results_root.mkdir()
    monkeypatch.setenv("MASS_ADK_RESULTS_ROOT", str(results_root))

    result = inspect_mass_checkpoint("../outside")

    assert result["error"].startswith("Invalid run_id")


def test_manifest_cache_is_clearable_after_env_changes():
    load_manifest.cache_clear()
    assert callable(load_manifest)
