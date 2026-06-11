"""Optimizer analyst subagent."""

from google.adk.agents import LlmAgent

from mass_adk.config import load_config
from mass_adk.tools import compare_experiments, get_experiment_summary

from .prompt import OPTIMIZER_ANALYST_PROMPT

optimizer_analyst_agent = LlmAgent(
    name="mass_optimizer_analyst",
    model=load_config().model,
    description="Explains MASS optimizer and mechanism-design ablation evidence.",
    instruction=OPTIMIZER_ANALYST_PROMPT,
    tools=[compare_experiments, get_experiment_summary],
)
