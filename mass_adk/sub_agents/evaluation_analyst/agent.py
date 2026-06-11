"""Evaluation analyst subagent."""

from google.adk.agents import LlmAgent

from mass_adk.config import load_config
from mass_adk.tools import compare_experiments, get_experiment_summary

from .prompt import EVALUATION_ANALYST_PROMPT

evaluation_analyst_agent = LlmAgent(
    name="mass_evaluation_analyst",
    model=load_config().model,
    description="Compares cached MASS results and explains evaluation caveats.",
    instruction=EVALUATION_ANALYST_PROMPT,
    tools=[compare_experiments, get_experiment_summary],
)
