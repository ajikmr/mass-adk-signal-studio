"""Signal analyst subagent."""

from google.adk.agents import LlmAgent

from mass_adk.config import load_config
from mass_adk.tools import get_experiment_summary, list_available_experiments

from .prompt import SIGNAL_ANALYST_PROMPT

signal_analyst_agent = LlmAgent(
    name="mass_signal_analyst",
    model=load_config().model,
    description="Explains MASS consensus, disagreement, and combined signal behavior.",
    instruction=SIGNAL_ANALYST_PROMPT,
    tools=[list_available_experiments, get_experiment_summary],
)
