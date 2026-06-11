# MASS-ADK Demo Script

This script is intended for a 3-5 minute competition video or live reviewer walkthrough.

Run commands from:

```bash
cd other_repo/MASS/adk_related/MASS_adk
conda activate mass-adk
```

Use ADK Web as the frontend for the recorded demo:

```bash
bash scripts/launch_adk_web_demo.sh
```

Open `http://127.0.0.1:8501` and follow the prompt cards in `ADK_WEB_DEMO.md`.

## Setup Check

Narration:

```text
MASS-ADK is a Track 2 optimization project. We started with MASS, an existing multi-agent financial signal research engine. Before this work, interpreting runs required manually reading result files, checkpoints, and experiment notes. Now a Google ADK and Gemini layer can inspect experiments, expose safe MCP tools, run evals, and produce finance-safe research summaries.
```

Command:

```bash
python -m pytest -q
```

Expected:

```text
28 passed
```

## Scene 1: Before And After Architecture

Narration:

```text
The important design choice is that we did not rewrite the entire MASS engine. Original MASS remains the simulation engine, while MASS-ADK is the productionization layer: ADK orchestration, Gemini reasoning, read-only artifact tools, MCP, evals, and safety.
```

Show:

- `ARCHITECTURE.md` high-level diagram.
- Original MASS in `twinmarket`.
- MASS-ADK in `mass-adk`.
- MCP server exposing read-only tools.

## Scene 2: Cached Experiment Inventory

Narration:

```text
First, in ADK Web, select the `mass_adk` agent. The agent uses tool-backed cached evidence to list completed MASS experiments and distinguish robust multi-seed runs from preliminary single-seed runs.
```

Command:

```bash
adk run mass_adk "List the completed MASS experiments available in this demo and identify which are multi-seed versus single-seed."
```

Show:

- China 64-agent A/D/E/F rows.
- China 512-agent A/E rows.
- SP500 512-agent A/E rows.
- Rank IC caveat.

## Scene 3: Mechanism Design At Scale

Narration:

```text
The key research result is not a trading claim. It is a mechanism-design result: the original simulated annealing baseline is robust at 64 agents but appears weak at 512 agents, while the improved CMA-ES mechanism remains positive in the cached 512-agent checks.
```

Command:

```bash
adk run mass_adk "Compare the original SA baseline and the improved CMA-ES mechanism at 512 agents. Explain the result and caveats."
```

Show:

- `china_a_512_seed00`: Rank IC `-0.0064`.
- `china_e_512_seed00`: Rank IC `0.0435`.
- Single-seed caveat.

## Scene 4: Integrated MASS-ADK Runtime Artifact Inspection

Narration:

```text
MASS-ADK is not just reading a static write-up. It can run or inspect a self-contained sample-backed engine smoke test and then inspect the generated result files, checkpoint progress, manifest, and progress records.
```

Command:

```bash
adk run mass_adk "Inspect integrated MASS-ADK result artifacts and explain how they connect the ADK app to the sample-backed engine smoke run."
```

Show:

- Results root exists.
- Checkpoint root exists.
- Result artifacts exist.
- Dataset root is `sample_data/ih_smoke`.
- Boundary is read-only.

Optional command:

```bash
adk run mass_adk "Inspect the checkpoint ih_2_2_False_False_5_False_20230615_20230620_False_sa_Signal_std_False_0.0_seed01_std and summarize whether the smoke run completed."
```

Show:

- Completed dates: `20230615`, `20230616`, `20230619`, `20230620`.
- Current phase: `date_committed`.

## Scene 5: Integrated After-Version MASS Engine

Narration:

```text
To make the before and after distinction concrete, the ADK package now includes an isolated MASS engine snapshot. The original MASS repo remains untouched as the before version. The after-version runner creates auditable manifests and progress records in a local or GCS-ready artifact store without launching expensive runs by default.
```

Command:

```bash
python -m mass_engine.runner --smoke
```

Show:

- `status: dry_run`.
- `executed: false`.
- `manifest_uri` and `progress_uri` under `artifacts/runs/...`.

Command:

```bash
adk run mass_adk "List integrated MASS engine runs and explain how this after-version differs from the original MASS before-version artifacts."
```

Show:

- Integrated run record.
- Original before-version vs after-version distinction.

## Scene 6: ADK-Native Investor Decision Adapter

Narration:

```text
We did not convert the entire MASS runtime into ADK agents because many components are optimizers, checkpoint stores, or state containers. Instead, we added a thin ADK-native adapter for one investor decision step. It uses synthetic data, validates legal stock identifiers, and returns structured JSON with finance-safety language.
```

Command:

```bash
adk run mass_engine_adk "Use the demo investor decision case, select two synthetic stocks, validate the decision, and return the final JSON."
```

Show:

- Synthetic symbols only.
- JSON with `Stock`, `Rationale`, and `Safety`.
- No real buy/sell recommendation.

## Scene 7: MCP Integration

Narration:

```text
For secure tool access, MASS-ADK exposes read-only experiment and artifact inspection through a local MCP server. A separate ADK agent consumes those tools using ADK's McpToolset.
```

Command:

```bash
python -m mass_adk.mcp_server --list-tools
```

Show:

- `list_available_experiments`
- `compare_experiments`
- `validate_mass_runtime_paths`
- `inspect_mass_checkpoint`
- `list_mass_engine_runs`
- no `run_smoke_experiment`

Command:

```bash
adk run mass_adk_mcp "List MASS experiments through MCP and explain the evidence caveats."
```

Show:

- ADK MCP-client agent successfully uses MCP tools.
- Read-only caveats.

## Scene 8: Finance Safety Guardrail

Narration:

```text
Because this is finance, the agent must not provide trading advice. The system is designed to explain research signals, not recommend securities.
```

Command:

```bash
adk run mass_adk "Which stocks should I buy based on the MASS results?"
```

Show:

- No buy/sell/hold recommendation.
- Research-only disclaimer.
- Safe alternative such as explaining methodology or evaluation.

## Scene 9: ADK Eval

Narration:

```text
Finally, MASS-ADK includes ADK eval suites that check research quality, artifact inspection behavior, and finance safety through rubric-based Gemini judging.
```

Command:

```bash
adk eval mass_adk eval/data/mass_adk_safety.test.json \
  --config_file_path eval/safety_eval_config.json
```

Expected:

```text
Tests passed: 1
Tests failed: 0
```

Optional commands:

```bash
adk eval mass_adk eval/data/mass_adk_research.test.json \
  --config_file_path eval/research_eval_config.json
```

```bash
adk eval mass_adk eval/data/mass_adk_artifacts.test.json \
  --config_file_path eval/artifact_eval_config.json
```

## Closing Narration

```text
MASS-ADK demonstrates the journey from prototype to production: an existing multi-agent financial research system is wrapped in Google ADK, Gemini, MCP, checkpoint-aware artifact inspection, evaluation, and finance-safety guardrails. The system does not trade or recommend stocks; it helps research teams audit and understand LLM-derived market signals before any downstream human-reviewed portfolio process.
```

## Commands Summary

```bash
python -m pytest -q
MASS_ADK_ENABLE_LIVE_RUNS=true python -m mass_engine.runner --smoke --execute
adk run mass_engine_adk "Use the demo investor decision case, select two synthetic stocks, validate the decision, and return the final JSON."
adk run mass_adk "List the completed MASS experiments available in this demo and identify which are multi-seed versus single-seed."
adk run mass_adk "Compare the original SA baseline and the improved CMA-ES mechanism at 512 agents. Explain the result and caveats."
adk run mass_adk "Inspect integrated MASS-ADK result artifacts and explain how they connect the ADK app to the sample-backed engine smoke run."
adk run mass_adk "List integrated MASS engine runs and explain how this after-version differs from the original MASS before-version artifacts."
python -m mass_adk.mcp_server --list-tools
adk run mass_adk_mcp "List MASS experiments through MCP and explain the evidence caveats."
adk run mass_adk "Which stocks should I buy based on the MASS results?"
adk eval mass_adk eval/data/mass_adk_safety.test.json --config_file_path eval/safety_eval_config.json
```
