import json
from pathlib import Path

import pytest

from mass_engine.cloud import create_artifact_store
from mass_engine.cloud.local_store import LocalArtifactStore
from mass_engine.runner import build_mass_command, build_run_id, main, parse_args
from mass_adk.tools import inspect_mass_engine_run, list_mass_engine_runs


def test_local_artifact_store_round_trip(tmp_path):
    store = LocalArtifactStore(tmp_path)

    uri = store.write_json("runs/test/manifest.json", {"run_id": "test"})
    store.write_bytes("runs/test/blob.bin", b"payload")

    assert Path(uri).exists()
    assert store.read_json("runs/test/manifest.json") == {"run_id": "test"}
    assert store.read_bytes("runs/test/blob.bin") == b"payload"
    assert store.exists("runs/test/blob.bin") is True
    assert store.list("runs/test") == ["runs/test/blob.bin", "runs/test/manifest.json"]


def test_local_artifact_store_rejects_path_escape(tmp_path):
    store = LocalArtifactStore(tmp_path)

    with pytest.raises(ValueError):
        store.write_json("../escape.json", {})

    with pytest.raises(ValueError):
        store.write_bytes(str(tmp_path / "absolute.bin"), b"bad")


def test_create_gcs_store_requires_bucket(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_STORAGE_BUCKET", raising=False)

    with pytest.raises(ValueError):
        create_artifact_store(backend="gcs")


def test_runner_builds_smoke_run_id_and_command(tmp_path):
    args = parse_args(
        [
            "--smoke",
            "--local_artifact_root",
            str(tmp_path),
            "--result_root",
            str(tmp_path / "results"),
        ]
    )

    run_id = build_run_id(args)
    command = build_mass_command(args, run_id)

    assert run_id == "ih_2_2_False_False_5_False_20230615_20230620_False_sa_Signal_std_False_0.0_seed01_std"
    assert "stock_disagreement.main" in command
    assert "--result_root" in command
    assert str(tmp_path / "results") in command


def test_runner_dry_run_writes_manifest_and_progress(tmp_path, capsys):
    returncode = main(
        [
            "--smoke",
            "--local_artifact_root",
            str(tmp_path),
            "--result_root",
            str(tmp_path / "results"),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    run_id = output["run_id"]

    assert returncode == 0
    assert output["progress"]["status"] == "dry_run"
    assert (tmp_path / "runs" / run_id / "manifest.json").exists()
    assert (tmp_path / "runs" / run_id / "progress.json").exists()


def test_runner_blocks_execute_without_guard(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("MASS_ADK_ENABLE_LIVE_RUNS", raising=False)
    returncode = main(
        [
            "--smoke",
            "--execute",
            "--local_artifact_root",
            str(tmp_path),
            "--result_root",
            str(tmp_path / "results"),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert returncode == 2
    assert output["progress"]["status"] == "blocked"
    assert "MASS_ADK_ENABLE_LIVE_RUNS" in output["progress"]["reason"]


def test_mass_adk_tools_inspect_integrated_engine_runs(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MASS_ADK_ARTIFACT_BACKEND", "local")
    monkeypatch.setenv("MASS_ADK_LOCAL_ARTIFACT_ROOT", str(tmp_path))
    main(
        [
            "--smoke",
            "--local_artifact_root",
            str(tmp_path),
            "--result_root",
            str(tmp_path / "results"),
        ]
    )
    capsys.readouterr()

    listed = list_mass_engine_runs()
    inspected = inspect_mass_engine_run(listed["runs"][0]["run_id"])

    assert listed["count"] == 1
    assert listed["runs"][0]["status"] == "dry_run"
    assert inspected["progress"]["status"] == "dry_run"
    assert inspected["manifest"]["mode"] == "smoke"


def test_mass_engine_inspection_rejects_path_escape(tmp_path, monkeypatch):
    monkeypatch.setenv("MASS_ADK_ARTIFACT_BACKEND", "local")
    monkeypatch.setenv("MASS_ADK_LOCAL_ARTIFACT_ROOT", str(tmp_path))

    result = inspect_mass_engine_run("../bad")

    assert result["error"].startswith("Invalid run_id")
