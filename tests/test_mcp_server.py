from mass_adk.mcp_server import list_tool_names


def test_mcp_server_exposes_read_only_tools():
    names = set(list_tool_names())
    assert "list_available_experiments" in names
    assert "compare_experiments" in names
    assert "validate_mass_runtime_paths" in names
    assert "inspect_mass_checkpoint" in names
    assert "list_mass_engine_runs" in names
    assert "inspect_mass_engine_run" in names
    assert "run_smoke_experiment" not in names
