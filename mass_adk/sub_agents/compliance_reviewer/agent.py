"""Compliance reviewer subagent."""

from google.adk.agents import LlmAgent

from mass_adk.config import load_config

from .prompt import COMPLIANCE_REVIEWER_PROMPT

compliance_reviewer_agent = LlmAgent(
    name="mass_compliance_reviewer",
    model=load_config().model,
    description="Checks MASS-ADK outputs for research-only finance safety language.",
    instruction=COMPLIANCE_REVIEWER_PROMPT,
)
