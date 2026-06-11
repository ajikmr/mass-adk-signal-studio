# MASS-ADK Signal Studio Submission Brief

## Project Summary

MASS-ADK Signal Studio is a Google ADK and Gemini-powered productionization layer for MASS, an existing multi-agent financial signal research system.

MASS originally runs long-horizon investor-agent simulations that generate stock-ranking signals and evaluate signal quality through metrics such as Rank IC and ICIR. MASS-ADK turns that research prototype into an auditable, tool-using, safety-guarded agent workflow that can inspect cached experiments, run a self-contained sample-backed engine smoke test, read integrated MASS-ADK artifacts, summarize checkpoints, run ADK evals, expose tools through MCP, and produce finance-safe research memos.

## Competition Track

Recommended track:

```text
Track 2: Optimize Existing Agents
```

Reason:

MASS was an existing experimental multi-agent finance system. MASS-ADK hardens it through Google ADK orchestration, Gemini analysis, MCP tool exposure, local artifact inspection, rubric-based evals, and safety guardrails.

## One-Liner

```text
MASS-ADK Signal Studio turns long-running multi-agent financial signal experiments into auditable, Gemini-powered research workflows with ADK orchestration, MCP tools, checkpoint visibility, evaluation, and finance-safe reporting.
```

## Problem

LLM-driven financial agents can generate useful research signals, but prototype systems often lack:

- reliable experiment inspection,
- reproducible evaluation workflows,
- checkpoint visibility,
- safe business-facing summaries,
- separation between signal quality and portfolio returns,
- secure tool access patterns.

This creates a gap between research prototypes and production-grade financial research workflows.

## Before And After Optimization

Before MASS-ADK:

- MASS was a powerful research engine, but interpretation required manually reading run files, notes, and checkpoint folders.
- Experiment outputs were not exposed through a standard agent tool interface.
- Finance-safety behavior was not tested through ADK eval.
- There was no MCP interface for secure read-only inspection.
- Demoing the system risked either running expensive simulations live or showing only static notes.

After MASS-ADK:

- Gemini/ADK agents can explain cached MASS evidence through tool-backed workflows.
- Read-only tools inspect integrated MASS-ADK result artifacts and checkpoint state.
- Rubric-based ADK evals test research quality, artifact behavior, and finance safety.
- MCP exposes safe inspection tools and excludes expensive live-run tools.
- The demo is deterministic, auditable, and grounded in cached evidence plus a self-contained sample-backed live smoke run.

This is the core Track 2 optimization story: moving an existing experimental agent system toward production reliability.

## Solution

MASS-ADK provides an ADK-native control and analysis layer around the existing MASS engine.

Core capabilities:

- Gemini-powered coordinator and specialist agents.
- Read-only tools for cached MASS experiment evidence.
- Read-only tools for integrated MASS-ADK result artifacts and checkpoints.
- Rubric-based ADK eval suites for research quality, artifact inspection, and finance safety.
- MCP stdio server exposing read-only experiment and artifact tools.
- Optional ADK MCP-client agent using `McpToolset`.
- Finance-safety prompts and evals that avoid buy/sell recommendations.

## Business Case

Target users:

- quant research teams,
- fintech startups,
- investment research platforms,
- portfolio-construction researchers,
- teams evaluating LLM-generated signals before downstream allocation.

Business value:

- reduces time to inspect and summarize complex LLM-agent experiments,
- makes experiment artifacts auditable for research teams,
- separates signal-generation evidence from investment recommendations,
- supports human-in-the-loop governance,
- provides a repeatable path from experimental agents to production-style workflows.

MASS-ADK is not an autonomous trading bot. It is a research and decision-support platform for signal evaluation.

## Technical Implementation

Architecture image:

```text
assets/architecture.png
```

Supporting flow diagrams:

```text
assets/native_adk_flow.png
assets/mcp_flow.png
```

Main ADK app:

```bash
adk run mass_adk
```

ADK Web frontend:

```bash
bash scripts/launch_adk_web_demo.sh
```

This starts ADK Web with MASS-ADK branding and exposes the three demo agents through the browser UI: `mass_adk`, `mass_engine_adk`, and `mass_adk_mcp`.

Optional MCP-client ADK app:

```bash
adk run mass_adk_mcp
```

Key implementation pieces:

| Component | File/Folder | Purpose |
| --- | --- | --- |
| Root ADK agent | `mass_adk/agent.py` | Gemini coordinator for research workflows |
| Specialist agents | `mass_adk/sub_agents/` | Data, signal, optimizer, evaluation, and compliance analysis |
| Cached evidence tools | `mass_adk/tools/evaluation_tools.py` | Experiment summaries and comparisons |
| Runtime artifact tools | `mass_adk/tools/artifact_tools.py` | Result/checkpoint inspection from integrated MASS-ADK outputs |
| Integrated engine | `mass_engine/` | Isolated after-version MASS runtime snapshot with guarded runner |
| ADK investor adapter | `mass_engine_adk/` | ADK-native synthetic investor decision step demo |
| Artifact store | `mass_engine/cloud/` | Local and GCS-ready artifact-store abstraction |
| MCP server | `mass_adk/mcp_server.py` | Read-only MCP tool server over stdio |
| MCP client agent | `mass_adk_mcp/agent.py` | ADK agent consuming MCP tools through `McpToolset` |
| Eval fixtures | `eval/data/` | Research, artifact, and safety eval prompts |
| Eval rubrics | `eval/*_eval_config.json` | LLM-as-judge rubric criteria |
| Reviewer guide | `REVIEWER_INSTRUCTIONS.md` | Commands and pass criteria for reviewers |

## Google Cloud And ADK Usage

Google technology used:

- Google ADK `LlmAgent` for the main agent workflow.
- ADK `AgentTool` for specialist subagents.
- ADK-native investor decision adapter for one synthetic MASS decision step.
- ADK `McpToolset` for the MCP-client variant.
- Gemini through Vertex AI with configurable model selection.
- ADK eval with rubric-based LLM-as-judge scoring.
- MCP server integration for secure read-only tool access.

Default model:

```bash
MASS_ADK_MODEL=gemini-3.5-flash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_LOCATION=global
```

Deployment-ready region variable:

```bash
MASS_ADK_DEPLOY_REGION=us-central1
```

## MASS vs MASS-ADK Boundary

| Layer | Environment | Responsibility |
| --- | --- | --- |
| Original MASS | `twinmarket` | Executes simulations, checkpoints, signal generation, and large offline experiments |
| Integrated MASS engine | `mass-adk` | After-version dry-run manifests, guarded smoke execution, and local/GCS-ready artifact routing |
| MASS-ADK | `mass-adk` | ADK/Gemini orchestration, artifact inspection, summaries, evals, MCP, and safety |

This boundary is intentional. Expensive 64-agent and 512-agent runs remain offline research jobs. MASS-ADK inspects their outputs and provides explainable, safe, auditable research workflows.

## Evidence Included In Demo

Cached MASS evidence:

| Study | Key result |
| --- | --- |
| China 64-agent baseline A | `10d Rank IC = 0.0331 +/- 0.0099` |
| China 64-agent D | `10d Rank IC = 0.0230 +/- 0.0055` |
| China 64-agent E | `10d Rank IC = 0.0205 +/- 0.0044` |
| China 64-agent F | `10d Rank IC = 0.0128 +/- 0.0255` |
| China E-512 | `10d Rank IC = 0.0435`, single seed |
| China A-512 | `10d Rank IC = -0.0064`, single seed |
| SP500 E-512 short window | `10d Rank IC = 0.0139 +/- 0.0067` |
| SP500 A-512 short window | `10d Rank IC = 0.0031`, single seed |

Integrated sample-backed smoke artifact evidence:

```text
artifacts/mass_engine/results/ih_2_2_False_False_5_False_20230615_20230620_False_sa_Signal_std_False_0.0_seed01_std.parq
artifacts/mass_engine/results/dist_ih_2_2_False_False_5_False_20230615_20230620_False_sa_Signal_std_False_0.0_seed01_std_5_positive.pkl
artifacts/mass_engine/results/checkpoints/ih_2_2_False_False_5_False_20230615_20230620_False_sa_Signal_std_False_0.0_seed01_std/
```

Checkpoint progress:

```text
completed_dates: 20230615, 20230616, 20230619, 20230620
current_phase: date_committed
last_committed_date: 20230620
```

Integrated after-version engine evidence:

```bash
python -m mass_engine.runner --smoke
```

This writes dry-run records under:

```text
artifacts/runs/<run_id>/manifest.json
artifacts/runs/<run_id>/progress.json
```

These records are inspectable through native ADK tools and through the read-only MCP server.

## Testing And Evaluation

Unit tests:

```bash
python -m pytest -q
```

Current unit-test validation:

```text
28 passed
```

The `mass-adk` environment now also includes the minimal copied-engine runtime
dependencies from the original MASS setup: `openai`, `backoff`, `retrying`,
`scipy`, `pyarrow`, `pandas`, `numpy`, `tqdm`, `pyyaml`, and `cma`.

ADK research eval:

```bash
adk eval mass_adk eval/data/mass_adk_research.test.json \
  --config_file_path eval/research_eval_config.json \
  --print_detailed_results
```

ADK artifact eval:

```bash
adk eval mass_adk eval/data/mass_adk_artifacts.test.json \
  --config_file_path eval/artifact_eval_config.json \
  --print_detailed_results
```

ADK safety eval:

```bash
adk eval mass_adk eval/data/mass_adk_safety.test.json \
  --config_file_path eval/safety_eval_config.json \
  --print_detailed_results
```

MCP tool listing:

```bash
python -m mass_adk.mcp_server --list-tools
```

Integrated engine dry-run:

```bash
python -m mass_engine.runner --smoke
```

The integrated smoke path uses bundled synthetic data under:

```text
sample_data/ih_smoke
sample_data/sp500_smoke
```

Reviewers do not need the original MASS research dataset for this test path.

The bundled sample data verifies execution plumbing only. It does not reproduce
or independently verify paper-scale empirical findings. The larger China/SP500
results in the curated manifest are reported benchmark evidence for the demo and
should be interpreted with the documented single-seed, short-window, and
signal-vs-return caveats.

Complete live sample-backed smoke test:

```bash
MASS_ADK_ENABLE_LIVE_RUNS=true python -m mass_engine.runner --smoke --execute
```

Integrated engine manifests distinguish:

```text
adk_model      # Gemini model used by ADK agents
engine_model   # MASS_MODEL_NAME / OPENAI_MODEL used by copied MASS live runs
```

Copied engine CLI import/help check:

```bash
env PYTHONPATH=mass_engine python -m stock_disagreement.main --help
```

ADK-native investor adapter:

```bash
adk run mass_engine_adk "Use the demo investor decision case, select two synthetic stocks, validate the decision, and return the final JSON."
```

Full instructions are in `REVIEWER_INSTRUCTIONS.md`.

Deployment notes and Google Cloud roadmap are in `DEPLOYMENT.md`.

ADK Web frontend guide and prompt cards are in `ADK_WEB_DEMO.md`.

## Demo Flow

Recommended video/demo sequence:

1. Show the before/after problem: manual MASS artifact interpretation vs ADK/Gemini inspection.
2. Show MASS vs MASS-ADK architecture.
3. Launch ADK Web as the lightweight frontend.
4. Run cached experiment inventory in `mass_adk`.
5. Compare China 512-agent SA vs CMA-ES mechanism.
6. Run or inspect the sample-backed integrated `mass_engine.runner --smoke --execute` smoke test.
7. Show integrated after-version manifest/progress/result/checkpoint records.
8. Show ADK-native synthetic investor decision adapter.
9. Run MCP-client agent to show MCP tool access.
10. Run safety prompt: “Which stocks should I buy?”
11. Show ADK eval result summary.

Detailed script is in `DEMO_SCRIPT.md`.

Devpost-style copy is available in `DEVPOST_SUBMISSION_DRAFT.md`.

Presentation guidance based on the official guide and past submissions is available in `PRESENTATION_STRATEGY.md`.

## Safety And Compliance

MASS-ADK enforces these boundaries:

- research-only use,
- no financial advice,
- no buy/sell/hold recommendations,
- no order execution,
- no claims of guaranteed returns,
- Rank IC is signal quality, not portfolio return,
- single-seed and short-window caveats must be stated.

## Limitations

- Artifact tools inspect metadata, checkpoint JSON, shard counts, and SQLite table counts; they do not parse parquet or pickle contents yet.
- SP500 transfer evidence is short-window and should not be treated as conclusive.
- China 512-agent evidence is single-seed in the cached manifest.
- Large MASS runs are intentionally not triggered by the default ADK app.
- Cloud Run / Agent Runtime are documented as roadmap deployment paths unless a hosted endpoint is explicitly validated.
- Full live execution from the integrated `mass_engine` snapshot remains guarded; current default is dry-run manifest/progress creation.

## Current Readiness

The project is ready for local reviewer testing and demo preparation.

Remaining submission assets:

- record final video,
- optionally deploy ADK app or provide local testing access,
- optionally validate GCS artifact smoke in the final project,
- optionally deploy ADK app or MCP service to Cloud Run / Agent Runtime.
