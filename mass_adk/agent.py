"""Root ADK agent for MASS-ADK Signal Studio."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from .config import load_config
from .prompt import ROOT_PROMPT
from .sub_agents.compliance_reviewer import compliance_reviewer_agent
from .sub_agents.data_analyst import data_analyst_agent
from .sub_agents.evaluation_analyst import evaluation_analyst_agent
from .sub_agents.optimizer_analyst import optimizer_analyst_agent
from .sub_agents.signal_analyst import signal_analyst_agent
from .tools import (
    compare_experiments,
    generate_research_memo,
    get_experiment_summary,
    inspect_mass_checkpoint,
    inspect_mass_engine_run,
    list_available_datasets,
    list_available_experiments,
    list_mass_checkpoints,
    list_mass_engine_runs,
    list_mass_result_artifacts,
    run_smoke_experiment,
    validate_mass_runtime_paths,
)

MODEL = load_config().model

root_agent = LlmAgent(
    name="mass_adk_signal_studio",
    model=MODEL,
    description=(
        "Research assistant for inspecting MASS multi-agent financial signal "
        "experiments, comparing cached benchmark results, and producing "
        "auditable research memos."
    ),
    instruction=ROOT_PROMPT,
    tools=[
        list_available_datasets,
        list_available_experiments,
        validate_mass_runtime_paths,
        list_mass_result_artifacts,
        list_mass_checkpoints,
        inspect_mass_checkpoint,
        list_mass_engine_runs,
        inspect_mass_engine_run,
        get_experiment_summary,
        compare_experiments,
        generate_research_memo,
        run_smoke_experiment,
        AgentTool(agent=data_analyst_agent),
        AgentTool(agent=signal_analyst_agent),
        AgentTool(agent=optimizer_analyst_agent),
        AgentTool(agent=evaluation_analyst_agent),
        AgentTool(agent=compliance_reviewer_agent),
    ],
)
