"""Data analyst subagent."""

from google.adk.agents import LlmAgent

from mass_adk.config import load_config
from mass_adk.tools import (
    inspect_mass_checkpoint,
    inspect_mass_engine_run,
    list_available_datasets,
    list_available_experiments,
    list_mass_checkpoints,
    list_mass_engine_runs,
    list_mass_result_artifacts,
    validate_mass_runtime_paths,
)

from .prompt import DATA_ANALYST_PROMPT

data_analyst_agent = LlmAgent(
    name="mass_data_analyst",
    model=load_config().model,
    description="Summarizes MASS datasets, stock pools, windows, and cached experiment availability.",
    instruction=DATA_ANALYST_PROMPT,
    tools=[
        list_available_datasets,
        list_available_experiments,
        validate_mass_runtime_paths,
        list_mass_result_artifacts,
        list_mass_checkpoints,
        inspect_mass_checkpoint,
        list_mass_engine_runs,
        inspect_mass_engine_run,
    ],
)
