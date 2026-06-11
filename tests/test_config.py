from pathlib import Path

from mass_adk.config import load_config


def test_default_model_is_gemini_35_flash(monkeypatch):
    monkeypatch.delenv("MASS_ADK_MODEL", raising=False)
    config = load_config(env_file=Path("/tmp/nonexistent_mass_adk_env"))
    assert config.model == "gemini-3.5-flash"


def test_live_runs_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MASS_ADK_ENABLE_LIVE_RUNS", raising=False)
    config = load_config(env_file=Path("/tmp/nonexistent_mass_adk_env"))
    assert config.enable_live_runs is False


def test_deploy_region_is_separate_from_model_location(monkeypatch):
    monkeypatch.delenv("MASS_ADK_DEPLOY_REGION", raising=False)
    config = load_config(env_file=Path("/tmp/nonexistent_mass_adk_env"))
    assert config.deploy_region == "us-central1"
