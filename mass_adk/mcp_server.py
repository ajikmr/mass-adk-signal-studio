"""Read-only MCP server for MASS-ADK artifact and experiment tools."""

from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Callable
from typing import Any

import mcp.server.stdio
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type
from mcp import types as mcp_types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from mass_adk.tools import (
    compare_experiments,
    get_experiment_summary,
    inspect_mass_checkpoint,
    inspect_mass_engine_run,
    list_available_datasets,
    list_available_experiments,
    list_mass_checkpoints,
    list_mass_engine_runs,
    list_mass_result_artifacts,
    validate_mass_runtime_paths,
)


SERVER_NAME = "mass-adk-readonly-mcp"
SERVER_VERSION = "0.1.0"

READ_ONLY_FUNCTIONS: list[Callable[..., dict[str, Any]]] = [
    list_available_datasets,
    list_available_experiments,
    get_experiment_summary,
    compare_experiments,
    validate_mass_runtime_paths,
    list_mass_result_artifacts,
    list_mass_checkpoints,
    inspect_mass_checkpoint,
    list_mass_engine_runs,
    inspect_mass_engine_run,
]

TOOLS = {FunctionTool(function).name: FunctionTool(function) for function in READ_ONLY_FUNCTIONS}

app = Server(SERVER_NAME)


def _json_text(payload: Any) -> list[mcp_types.TextContent]:
    return [mcp_types.TextContent(type="text", text=json.dumps(payload, indent=2))]


@app.list_tools()
async def list_mcp_tools() -> list[mcp_types.Tool]:
    """List read-only MASS-ADK tools exposed through MCP."""

    return [adk_to_mcp_tool_type(tool) for tool in TOOLS.values()]


@app.call_tool()
async def call_mcp_tool(name: str, arguments: dict[str, Any]) -> list[mcp_types.Content]:
    """Call one read-only MASS-ADK tool by name."""

    tool = TOOLS.get(name)
    if tool is None:
        return _json_text(
            {
                "error": f"Unknown MCP tool: {name}",
                "available_tools": sorted(TOOLS),
            }
        )

    try:
        result = await tool.run_async(args=arguments or {}, tool_context=None)
    except Exception as exc:  # pragma: no cover - defensive MCP boundary.
        return _json_text({"error": f"Tool {name} failed: {exc}"})
    return _json_text(result)


async def run_mcp_stdio_server() -> None:
    """Run the MCP server over stdio."""

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=SERVER_NAME,
                server_version=SERVER_VERSION,
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def list_tool_names() -> list[str]:
    """Return exposed MCP tool names for tests and CLI smoke checks."""

    return sorted(TOOLS)


def main() -> None:
    """CLI entrypoint.

    `--list-tools` is a non-MCP smoke check that writes to stdout. Normal MCP
    stdio mode must not print banner text because stdout is the protocol stream.
    """

    if "--list-tools" in sys.argv:
        print(json.dumps({"tools": list_tool_names()}, indent=2))
        return
    asyncio.run(run_mcp_stdio_server())


if __name__ == "__main__":
    main()
