"""Optional ADK agent that consumes MASS-ADK tools through MCP."""

from __future__ import annotations

import sys

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from mass_adk.config import load_config


MCP_CLIENT_PROMPT = """
You are the MASS-ADK MCP client agent. Use the read-only MCP tools exposed by
`mass_adk.mcp_server` to inspect cached MASS evidence and local MASS runtime
artifacts.

Important boundaries:
- The MCP tools are read-only.
- Do not launch expensive MASS simulations.
- Do not recommend buying or selling securities.
- Rank IC is signal quality, not realized portfolio return.
- Do not claim that any experiment guarantees returns, robustness, or future
  performance; multi-seed evidence only improves confidence relative to
  single-seed evidence.
- When inspecting artifacts, only claim what tools return: paths, filenames,
  checkpoint JSON, shard counts, and SQLite table counts.
"""

root_agent = LlmAgent(
    name="mass_adk_mcp_client",
    model=load_config().model,
    description=(
        "MCP-client variant of MASS-ADK that consumes read-only experiment and "
        "artifact tools from the local MASS-ADK MCP server."
    ),
    instruction=MCP_CLIENT_PROMPT,
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=sys.executable,
                    args=["-m", "mass_adk.mcp_server"],
                )
            ),
            tool_filter=[
                "list_available_datasets",
                "list_available_experiments",
                "get_experiment_summary",
                "compare_experiments",
                "validate_mass_runtime_paths",
                "list_mass_result_artifacts",
                "list_mass_checkpoints",
                "inspect_mass_checkpoint",
                "list_mass_engine_runs",
                "inspect_mass_engine_run",
            ],
        )
    ],
)
