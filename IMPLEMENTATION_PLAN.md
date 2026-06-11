# MASS-ADK Implementation Plan

## Purpose

This folder contains the ADK-based version of MASS for the Google for Startups AI Agents Challenge.

The goal is to package MASS as a Google ADK/Gemini-powered financial research and signal-generation system, not as an autonomous trading bot. The submission should demonstrate how an existing multi-agent finance prototype can be refactored into a production-oriented agent workflow with tool use, evaluation, checkpointing, and auditable research outputs.

Working product name:

```text
MASS-ADK Signal Studio
```

Primary competition track:

```text
Track 2: Optimize Existing Agents
```

Secondary framing:

```text
Prototype-to-production refactor of a multi-agent financial signal research system using Google ADK, Gemini, MCP-style tools, and Google Cloud deployment paths.
```

## Submission Positioning

MASS-ADK should be presented as a decision-support and research platform for portfolio-construction signals.

It should not be presented as:

- an autonomous trading system
- investment advice
- an order-execution system
- a promise of financial returns

Core value proposition:

```text
MASS-ADK helps quant researchers and fintech teams generate, inspect, and evaluate LLM-derived stock-ranking signals through an auditable multi-agent workflow.
```

## Default Model Configuration

All Gemini model configuration should be read from `.env` so the model can be swapped without code changes.

Default model:

```bash
MASS_ADK_MODEL=gemini-3.5-flash
```

Expected `.env` variables:

```bash
MASS_ADK_MODEL=gemini-3.5-flash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name
MASS_ADK_DEPLOY_REGION=us-central1
```

Optional local/dev variables:

```bash
MASS_ADK_DATASET_ROOT=./sample_data/ih_smoke
MASS_ADK_SP500_DATA_ROOT=./sample_data/sp500_smoke
MASS_ADK_RESULTS_ROOT=./artifacts/mass_engine/results
MASS_ADK_ENABLE_LIVE_RUNS=false
MASS_ADK_DEFAULT_STOCK_POOL=sp500
MASS_ADK_DEFAULT_EVAL_LABEL=10
```

Implementation rule:

- agents and tools should call a shared config helper instead of hardcoding model names or repository paths
- `.env.example` should include safe placeholders only
- no API keys or private credentials should be committed

## MASS vs MASS-ADK Operating Model

The project now uses original MASS as the unchanged before-version and MASS-ADK as the integrated after-version, with a clear boundary between them.

| Layer | Location | Environment | Responsibility |
| --- | --- | --- | --- |
| Original MASS engine | `other_repo/MASS/stock_disagreement/` | `twinmarket` | Before-version research runtime. Kept untouched for historical experiments and large offline studies. |
| Integrated MASS engine | `other_repo/MASS/adk_related/MASS_adk/mass_engine/` | `mass-adk` | After-version runtime snapshot with bundled smoke sample data, guarded execution, checkpoints, and local/GCS-ready artifact records. |
| MASS-ADK control layer | `other_repo/MASS/adk_related/MASS_adk/mass_adk/` | `mass-adk` | Orchestrates ADK/Gemini agents, reads cached evidence and engine artifacts, evaluates outputs, exposes MCP tools, generates reports, and enforces finance-safety constraints. |
| ADK investor adapter | `other_repo/MASS/adk_related/MASS_adk/mass_engine_adk/` | `mass-adk` | Demonstrates one MASS-style investor decision step as an ADK-native synthetic-data agent without rewriting the full engine. |

This is the correct near-term design for Track 2: Optimize Existing Agents. The submission story is that MASS was an existing experimental multi-agent finance system, and MASS-ADK is the ADK/Gemini productionization layer that makes it inspectable, evaluable, safer, and easier to demonstrate.

Do not rewrite the entire MASS simulator inside ADK before the competition deadline. The current design keeps the full simulation mechanics as Python engine code and adds a thin ADK-native adapter only where it improves the demo.

### Integration Roadmap

Phase 0, current validated state:

- MASS-ADK runs as an ADK app using Gemini through Vertex AI.
- Cached MASS evidence is available through a curated manifest.
- ADK eval runs with rubric-based criteria.
- Original MASS remains runnable separately in `twinmarket` as the before-version.
- Integrated `mass_engine` runs in `mass-adk` using bundled synthetic smoke data under `sample_data/`.
- Live integrated smoke execution has completed successfully with `MASS_ADK_ENABLE_LIVE_RUNS=true`.

Phase 1, implemented artifact and eval layer:

- Add tools that inspect original MASS output folders, integrated MASS engine artifacts, and checkpoint folders without launching new runs. Done for result artifacts, checkpoint summaries, and integrated run records.
- Add stable ADK prompts/evals for SP500 transfer, China 512-agent comparison, and research memo generation. Done for the current demo set.
- Keep all tools read-only by default.
- Current artifact tools inspect paths, filenames, checkpoint JSON, shard counts, and SQLite table counts. Parquet/pickle content parsing is a later enhancement.

Phase 2, guarded execution:

- Add an optional live smoke-run wrapper behind `MASS_ADK_ENABLE_LIVE_RUNS=true`. Done through `python -m mass_engine.runner --smoke --execute`.
- Restrict live runs to tiny configurations such as 2 investor types x 2 agents, 5 stocks, and a few trading days.
- Run large 64-agent and 512-agent studies offline through original MASS, not through default ADK interactions.
- Bundled `sample_data` verifies pipeline execution only; it is not research evidence.

Phase 3, MCP and Cloud architecture:

- Expose read-only MASS artifact and integrated engine tools through MCP. Done for local stdio MCP.
- Optionally deploy the MCP server or ADK app on Cloud Run / Agent Runtime.
- Treat expensive MASS runs as Cloud Run Jobs, batch jobs, or external research jobs whose artifacts are later inspected by MASS-ADK.

Phase 4, later native refactor:

- Only after the competition, consider porting additional selected MASS internals into ADK-native workflow agents if the tool/service boundary proves too limiting.
- Keep the separation unless there is a concrete reason to merge dependencies.

## Target User Flow

The first demo should support this interaction:

1. User asks for a MASS study summary on SP500 or China `ih`.
2. ADK coordinator identifies available cached experiments.
3. Data/result tools inspect available result files and metadata.
4. Evaluation tool reports Rank IC, ICIR, seed variance, and relevant caveats.
5. Agent explains consensus vs disagreement and optimizer-mechanism choices.
6. Agent generates a human-readable research memo with disclaimers.
7. Optional smoke mode runs a very small live MASS experiment if enabled.

The live judging demo should primarily use cached benchmark artifacts plus the bundled self-contained smoke dataset. Tiny live runs are supported but should be clearly marked as smoke tests, not research evidence.

## Proposed ADK Architecture

Initial package layout:

```text
MASS_adk/
  IMPLEMENTATION_PLAN.md
  README.md
  SUBMISSION.md
  DEVPOST_SUBMISSION_DRAFT.md
  PRESENTATION_STRATEGY.md
  ARCHITECTURE.md
  DEMO_SCRIPT.md
  ADK_WEB_DEMO.md
  DEPLOYMENT.md
  REVIEWER_INSTRUCTIONS.md
  pyproject.toml
  environment.yml
  .env.example
  assets/
    architecture.mmd
    architecture.png
    native_adk_flow.mmd
    native_adk_flow.png
    mcp_flow.mmd
    mcp_flow.png
  sample_data/
    README.md
    ih_smoke/
    sp500_smoke/
  scripts/
    create_smoke_sample_data.py
    launch_adk_web_demo.sh
  mass_adk/
    __init__.py
    agent.py
    config.py
    mcp_server.py
    prompt.py
    tools/
      __init__.py
      artifact_tools.py
      dataset_tools.py
      engine_artifact_tools.py
      experiment_tools.py
      evaluation_tools.py
      report_tools.py
    sub_agents/
      __init__.py
      data_analyst/
        __init__.py
        agent.py
        prompt.py
      signal_analyst/
        __init__.py
        agent.py
        prompt.py
      optimizer_analyst/
        __init__.py
        agent.py
        prompt.py
      evaluation_analyst/
        __init__.py
        agent.py
        prompt.py
      compliance_reviewer/
        __init__.py
        agent.py
        prompt.py
  tests/
    test_config.py
    test_tools.py
    test_artifact_tools.py
    test_mass_engine.py
    test_mass_engine_adk.py
    test_mcp_server.py
    test_sample_data.py
  eval/
    data/
      mass_adk.test.json
  mass_adk_mcp/
    __init__.py
    agent.py
  mass_engine/
    __init__.py
    runner.py
    cloud/
    stock_disagreement/
  mass_engine_adk/
    __init__.py
    agent.py
    prompts.py
    tools.py
```

Root coordinator:

- implemented as an ADK `LlmAgent`
- uses `AgentTool` to call specialist subagents
- uses Gemini model from `.env`
- produces final research reports and demo-ready explanations

Specialist agents:

| Agent | Responsibility |
| --- | --- |
| `data_analyst` | Identify datasets, stock pools, date ranges, and result availability |
| `signal_analyst` | Explain MASS consensus/disagreement signals and available signal files |
| `optimizer_analyst` | Explain SA vs CMA-ES, learned alpha, turnover penalty, and scale behavior |
| `evaluation_analyst` | Summarize IC, Rank IC, ICIR, seed statistics, and benchmark comparisons |
| `compliance_reviewer` | Ensure output is research-only, caveated, and not financial advice |

Tool layer:

| Tool | First implementation |
| --- | --- |
| `list_available_experiments` | List cached benchmark experiments from the curated manifest |
| `get_experiment_summary` | Return metrics for known China/SP500 experiments from curated JSON/Markdown |
| `compare_experiments` | Compare A/D/E/F/E-512/A-512 results |
| `validate_mass_runtime_paths` | Confirm self-contained package, sample data, result, and checkpoint paths |
| `list_mass_result_artifacts` | List integrated engine `.parq` and `.pkl` result files |
| `list_mass_checkpoints` | List copied-engine checkpoint directories |
| `inspect_mass_checkpoint` | Inspect checkpoint manifest/progress/shard/SQLite metadata |
| `list_mass_engine_runs` | List integrated `mass_engine.runner` run manifests/progress records |
| `inspect_mass_engine_run` | Inspect one integrated run record |
| `generate_research_memo` | Format a report from tool outputs |
| `run_smoke_experiment` | Optional tiny live run, disabled by default |

## MCP Strategy

MCP is included as a local read-only stdio server. It exposes selected native tools through MCP:

```text
list_available_experiments
get_experiment_summary
compare_experiments
inspect_checkpoint
list_mass_engine_runs
inspect_mass_engine_run
```

Recommended MCP deployment pattern:

- local stdio MCP server for development and video demo
- optional Streamable HTTP MCP server on Cloud Run for production-style architecture

Security constraints:

- expose read-only experiment and dataset inspection first
- do not expose arbitrary file reads
- do not expose expensive live runs unless explicitly enabled by environment variable
- filter tools in ADK `McpToolset` if an MCP client path is added

## Data And Result Strategy

The demo should rely on a curated manifest of already completed experiments rather than requiring judges to run expensive LLM workloads.

Initial curated results should include:

| Study | Key result |
| --- | --- |
| China 64-agent baseline A | `10d Rank IC = 0.0331 +/- 0.0099` |
| China 64-agent D | `10d Rank IC = 0.0230 +/- 0.0055` |
| China 64-agent E | `10d Rank IC = 0.0205 +/- 0.0044` |
| China 64-agent F | `10d Rank IC = 0.0128 +/- 0.0255` |
| China E-512 | `10d Rank IC = 0.0435` |
| China A-512 | `10d Rank IC = -0.0064` |
| SP500 E-512 short window | `10d Rank IC = 0.0139 +/- 0.0067` over 3 seeds |
| SP500 A-512 short window | `10d Rank IC = 0.0031` at seed 42 |

The agent should clearly distinguish:

- cached historical research evidence
- live smoke-test output
- bundled synthetic sample data
- limitations and single-seed caveats
- signal quality metrics vs actual portfolio returns

## Implementation Milestones

### Milestone 1: ADK Skeleton

- [x] Add `pyproject.toml`
- [x] Add `environment.yml` for a dedicated `mass-adk` conda env
- [x] Add `.env.example`
- [x] Add package skeleton under `mass_adk/`
- [x] Add `config.py` with `.env` loading and default `gemini-3.5-flash`
- [x] Add root `agent.py` with coordinator agent
- [x] Verify root agent imports in the dedicated `mass-adk` env
- [x] Verify a real `adk run mass_adk` query after Google/Gemini credentials are configured

### Milestone 2: Read-Only MASS Tools

- [x] Add curated experiment manifest
- [x] Add tool to list available experiments
- [x] Add tool to fetch one experiment summary
- [x] Add tool to compare experiments
- [x] Add unit tests for manifest and comparison logic

### Milestone 3: Specialist Subagents

- [x] Add data analyst agent
- [x] Add signal analyst agent
- [x] Add optimizer analyst agent
- [x] Add evaluation analyst agent
- [x] Add compliance reviewer agent
- [x] Wire subagents into root coordinator with `AgentTool`

### Milestone 4: Report Generation Demo

- [x] Implement one stable prompt path: “summarize the SP500 MASS transfer study”
- [x] Implement one stable prompt path: “compare China A-512 vs E-512”
- [x] Generate markdown research memo with disclaimers
- [x] Add ADK eval cases for research, artifact inspection, and safety prompts

### Milestone 5: Optional Live Smoke Run

- [x] Wrap tiny MASS run command behind `MASS_ADK_ENABLE_LIVE_RUNS`
- [x] Keep live run small enough for demos
- [x] Ensure checkpoint/resume paths are documented
- [x] Add read-only tools to inspect MASS results and checkpoint artifacts
- [x] Add bundled synthetic `sample_data` for self-contained reviewer smoke testing
- [x] Use generic macro filenames in all smoke datasets
- [x] Validate live sample-backed smoke run end-to-end
- [x] Never trigger expensive 512-agent runs from default agent behavior

### Milestone 6: MCP Integration

- [x] Add local MCP server exposing read-only experiment tools
- [x] Add ADK agent variant or toolset using `McpToolset`
- [x] Document local MCP demo command
- [ ] Optional: document Cloud Run MCP deployment pattern

### Milestone 7: Competition Package

- [x] Add architecture diagram
- [x] Add README with setup, run, demo prompts, and disclaimers
- [x] Add short video script
- [x] Add testing/demo access instructions
- [x] Add Google Cloud deployment notes for Agent Runtime or Cloud Run

## Demo Prompts

Initial demo prompts to support:

```text
Summarize the strongest MASS-ADK evidence for SP500 transfer and explain the caveats.
```

```text
Compare the original SA baseline and the improved CMA-ES mechanism at 512 agents.
```

```text
Generate a research memo for a quant lead explaining whether MASS should be used as an upstream signal generator for portfolio construction.
```

```text
List the completed MASS experiments available in this demo and identify which are multi-seed versus single-seed.
```

## Compliance And Safety Requirements

Every final research report should include:

- this is for research and educational use only
- this is not financial advice
- signals are not portfolio returns
- past signal quality does not guarantee future performance
- human review is required before any investment decision

The agent should avoid:

- recommending users buy or sell specific securities
- claiming guaranteed returns
- generating order instructions
- hiding single-seed limitations
- presenting SP500 transfer evidence as conclusive

## Open Design Decisions

- Should the first implementation use only native ADK function tools, or include MCP from the start? Resolved: both native tools and read-only MCP are included.
- Should curated experiment data live in JSON, Markdown, or generated from existing result files?
- Should live smoke runs call the copied engine directly or remain dry-run only? Resolved: copied-engine live smoke is supported behind `MASS_ADK_ENABLE_LIVE_RUNS=true`.
- Should the first deployed demo target ADK Web, Agent Runtime, or Cloud Run?
- How much of the original MASS code should be imported directly versus treated as an external tool layer? Resolved for submission: isolated copied `mass_engine` plus thin ADK adapter, not a full ADK rewrite.

Current recommendation:

1. Use `mass_adk` for the main demo and `mass_adk_mcp` for explicit MCP demonstration.
2. Use bundled `sample_data` for self-contained smoke execution.
3. Use cached results for benchmark evidence and keep smoke metrics separate from research claims.
4. Keep live runs optional, guarded, and small.

## Update Log

| Date | Update |
| --- | --- |
| 2026-06-08 | Created initial implementation plan for `MASS_adk`. |
| 2026-06-08 | Added ADK skeleton, dedicated `mass-adk` conda env definition, `.env.example`, cached experiment manifest, read-only tools, specialist subagents, README, eval fixture, and unit tests. |
| 2026-06-08 | Created the `mass-adk` conda environment and validated tests, ADK CLI availability, and root agent import with default model `gemini-3.5-flash`. |
| 2026-06-08 | Documented Vertex AI `404 NOT_FOUND` troubleshooting for model/location mismatch and recommended `GOOGLE_CLOUD_LOCATION=us-central1` or `global` for Gemini model access. |
| 2026-06-08 | Validated real local ADK execution through Vertex AI with `GOOGLE_CLOUD_LOCATION=global`; updated docs to treat `global` as the known-good default for `gemini-3.5-flash`. |
| 2026-06-08 | Added `MASS_ADK_DEPLOY_REGION` so future deployment region is tracked separately from Gemini model-serving location. |
| 2026-06-08 | Added ADK eval extra dependency and corrected eval command to use `adk eval mass_adk ...` rather than `mass_adk/__init__.py`. |
| 2026-06-08 | Added rubric-based `eval/eval_config.json` because default exact tool-trajectory and ROUGE criteria are too brittle for MASS research summaries. |
| 2026-06-08 | Documented the operating model: original MASS remains the experiment engine in `twinmarket`, while MASS-ADK is the ADK/Gemini control, analysis, evaluation, and demo layer in `mass-adk`. |
| 2026-06-08 | Validated original MASS tiny China smoke run and added read-only MASS artifact/checkpoint inspection tools to the ADK app. |
| 2026-06-08 | Tightened prompts and docs to avoid overclaiming artifact parsing; current artifact tools inspect metadata and checkpoint state only. |
| 2026-06-08 | Added formal reviewer instructions plus targeted ADK eval sets/configs for research summaries, artifact inspection, and finance safety. |
| 2026-06-08 | Added read-only stdio MCP server plus optional `mass_adk_mcp` ADK MCP-client agent for explicit MCP demonstration. |
| 2026-06-08 | Added `SUBMISSION.md`, `ARCHITECTURE.md`, and `DEMO_SCRIPT.md` to package the project for competition review and video/demo preparation. |
| 2026-06-08 | Reviewed official challenge guide and past submissions; added Devpost-style submission draft and presentation strategy emphasizing Track 2 before/after reliability. |
| 2026-06-08 | Added isolated `mass_engine` after-version snapshot, local/GCS-ready artifact stores, guarded dry-run runner, ADK/MCP inspection tools, and tests. |
| 2026-06-08 | Added `mass_engine_adk` synthetic investor decision adapter to demonstrate one MASS decision step as an ADK-native agent without rewriting the full engine. |
| 2026-06-08 | Added minimal copied-engine runtime dependencies to `mass-adk` and validated copied engine CLI help, dry-run, dependency imports, ADK agents, and MCP tools in the same conda env. |
| 2026-06-10 | Added self-contained synthetic smoke datasets under `sample_data`, switched integrated engine defaults away from original MASS data, validated live sample-backed smoke execution, and standardized generic macro filenames across `ih_smoke` and `sp500_smoke`. |
| 2026-06-10 | Exported Mermaid architecture diagrams to PNG assets and linked them from README, architecture, and submission documents. |
| 2026-06-10 | Added `DEPLOYMENT.md` covering validated local modes, MCP, optional GCS artifact smoke, and Cloud Run / Agent Runtime roadmap. |
| 2026-06-10 | Added ADK Web frontend guide and launch script so demos use the official ADK Web UI with prompt cards for `mass_adk`, `mass_engine_adk`, and `mass_adk_mcp`. |
