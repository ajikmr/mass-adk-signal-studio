"""ADK-native investor decision adapter for MASS-ADK."""

from google.adk.agents import LlmAgent

from mass_adk.config import load_config

from .prompts import INVESTOR_DECISION_PROMPT
from .tools import get_demo_investor_decision_case, validate_investor_decision


root_agent = LlmAgent(
    name="mass_engine_investor_decision_adapter",
    model=load_config().model,
    description=(
        "ADK-native adapter that demonstrates one MASS investor decision step "
        "using synthetic data, structured JSON output, and finance-safety rules."
    ),
    instruction=INVESTOR_DECISION_PROMPT,
    tools=[get_demo_investor_decision_case, validate_investor_decision],
)
