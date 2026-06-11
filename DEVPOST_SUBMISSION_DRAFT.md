# Devpost Submission Draft

This document is written in the style commonly used by successful hackathon and startup competition submissions. It can be copied into the final submission form and shortened as needed.

## Project Title

```text
MASS-ADK Signal Studio
```

## Tagline

```text
From multi-agent finance prototype to auditable ADK/Gemini signal research workflow.
```

## Track

```text
Optimize Existing Agents
```

## Inspiration

Financial research teams are increasingly experimenting with LLM agents, but most prototypes are difficult to trust in production. They often run expensive simulations, write scattered artifacts, and produce promising metrics without a clear way to audit what happened, explain the evidence, or prevent unsafe investment-advice claims.

We already had MASS, a multi-agent financial signal research system that simulates heterogeneous investor agents and evaluates stock-ranking signals through Rank IC and ICIR. The challenge was not inventing another finance chatbot. The challenge was turning an existing research prototype into something closer to a production-grade research workflow: inspectable, evaluable, safe, and connected through modern agent tooling.

## What It Does

MASS-ADK Signal Studio helps quant and fintech teams inspect, compare, and explain LLM-derived stock-ranking signal experiments.

It can:

- list completed MASS experiments across China and SP500 datasets,
- compare baseline and improved multi-agent mechanisms,
- explain consensus, disagreement, optimizer choice, learned alpha, and turnover penalty,
- inspect local MASS runtime artifacts and checkpoint folders,
- distinguish robust multi-seed evidence from preliminary single-seed evidence,
- expose read-only experiment and artifact tools through MCP,
- run ADK evals for research quality, artifact inspection, and finance safety,
- generate research-only memos with explicit no-financial-advice caveats.

It does not trade, execute orders, or recommend securities. It is a research and governance layer for financial signal experiments.

## Before And After

Before MASS-ADK:

- MASS experiments were powerful but mostly operated as research scripts.
- Result interpretation required manually reading files, notes, and checkpoint folders.
- There was no ADK-native research assistant to explain experiment evidence.
- There was no formal ADK eval suite for response quality or finance safety.
- There was no MCP interface for secure tool access.
- It was easy to overstate signal-quality metrics as portfolio performance if caveats were not enforced.

After MASS-ADK:

- Gemini/ADK agents can inspect cached MASS evidence and original runtime artifacts.
- Read-only tools summarize result files, checkpoints, progress state, and SQLite state counts.
- ADK evals test research summaries, artifact explanations, and no-advice behavior.
- A local MCP server exposes safe inspection tools only.
- A separate ADK MCP-client agent demonstrates MCP tool consumption through `McpToolset`.
- Finance-safety prompts and rubrics enforce research-only framing.

This is the core Track 2 story: an existing experimental agent system was hardened into a more reliable and auditable workflow.

## How We Built It

We built MASS-ADK as a separate ADK application around the original MASS runtime.

Original MASS remains the experiment engine:

```text
other_repo/MASS/stock_disagreement/main.py
```

MASS-ADK is the ADK control, inspection, eval, and reporting layer:

```text
other_repo/MASS/adk_related/MASS_adk/
```

Core components:

- Google ADK `LlmAgent` root coordinator.
- Specialist ADK agents for data, signal, optimizer, evaluation, and compliance review.
- Gemini through Vertex AI with model selection via `.env`.
- Native ADK function tools for cached experiment summaries and comparisons.
- Read-only artifact tools for MASS result files and checkpoint folders.
- ADK eval fixtures with rubric-based Gemini judging.
- MCP stdio server exposing only read-only inspection tools.
- Optional `mass_adk_mcp` agent that consumes MCP tools through ADK `McpToolset`.

Architecture assets:

```text
ARCHITECTURE.md
assets/architecture.png
assets/native_adk_flow.png
assets/mcp_flow.png
```

Demo frontend:

```text
ADK Web, launched by scripts/launch_adk_web_demo.sh
Prompt cards in ADK_WEB_DEMO.md
```

## Google Technologies Used

- Google Agent Development Kit for agent orchestration.
- Gemini through Vertex AI for reasoning and research summaries.
- ADK `AgentTool` for specialist subagent composition.
- ADK `McpToolset` for MCP-client integration.
- ADK eval for rubric-based quality and safety testing.
- Google Cloud authentication through Application Default Credentials.
- Planned deployment path through Agent Runtime or Cloud Run.
- Integrated after-version `mass_engine` snapshot with local/GCS-ready artifact-store routing.
- ADK-native synthetic investor decision adapter for one MASS-style decision step.

## Evidence And Validation

Cached MASS evidence includes:

- China 64-agent baseline A: `10d Rank IC = 0.0331 +/- 0.0099`.
- China 512-agent improved E: `10d Rank IC = 0.0435`, single seed.
- China 512-agent baseline A: `10d Rank IC = -0.0064`, single seed.
- SP500 512-agent improved E short-window transfer: `10d Rank IC = 0.0139 +/- 0.0067`.
- SP500 512-agent baseline A short-window comparator: `10d Rank IC = 0.0031`, single seed.

MASS-ADK intentionally presents these as signal-quality metrics, not portfolio returns.

The original MASS runtime was also validated with a tiny smoke run that produced result artifacts and a checkpoint folder with four committed dates: `20230615`, `20230616`, `20230619`, and `20230620`.

The after-version integrated engine can also create auditable dry-run records:

```bash
python -m mass_engine.runner --smoke
```

This writes `manifest.json` and `progress.json` under `artifacts/runs/<run_id>/`, proving the packaged engine can route run metadata through a local or GCS-ready artifact-store boundary without touching the original MASS repo.

Unit tests currently pass:

```text
28 passed
```

ADK eval suites cover research summaries, artifact inspection, and finance safety.

## Challenges We Ran Into

### Model Region Mismatch

`gemini-3.5-flash` was visible in Google Cloud Agent Studio, but local Vertex calls failed in `asia-south1`. We resolved this by using `GOOGLE_CLOUD_LOCATION=global` for model serving.

### Avoiding A Superficial ADK Wrapper

A static manifest reader would not be a strong submission. We added a self-contained sample-backed MASS engine smoke path plus read-only links to integrated result artifacts and checkpoints, so the ADK layer can inspect actual outputs generated by the packaged after-version engine.

### Financial Safety

Finance agents can easily be misinterpreted as trading advisors. We added explicit prompts, compliance review, eval rubrics, and demo prompts to ensure the system does not recommend securities or equate Rank IC with returns.

### Keeping Expensive Runs Controlled

Full 64-agent and 512-agent MASS runs are expensive. We intentionally keep large runs offline and expose inspection tools by default. The MCP layer excludes live-run tools.

## Accomplishments

- Built a working Google ADK application around an existing multi-agent finance engine.
- Added an isolated after-version MASS engine snapshot without modifying the original before-version repo.
- Added a thin ADK-native investor decision adapter instead of forcing the whole MASS runtime into ADK abstractions.
- Added Gemini-powered research summaries and specialist subagents.
- Added local/GCS-ready run manifest and progress artifact stores.
- Added artifact and checkpoint inspection for original MASS outputs.
- Added read-only MCP server and ADK MCP-client variant.
- Added ADK evals for research quality, artifacts, and finance safety.
- Produced reviewer instructions, architecture diagrams, demo script, and submission brief.

## What We Learned

- Track 2 submissions should emphasize reliability and before-vs-after hardening, not only features.
- ADK is useful as a productionization layer around an existing agentic engine.
- MCP is a natural boundary for safe, read-only tool exposure.
- Finance agents need explicit metric semantics and safety constraints.
- Cached evidence plus real artifact inspection is more reliable for demos than trying to run expensive live simulations during judging.

## What's Next

- Deploy MASS-ADK to Agent Runtime or Cloud Run.
- Store MASS artifacts in GCS and inspect them through the same tool interface.
- Add richer parquet/pickle parsing for result summaries.
- Add observability traces and saved demo sessions.
- Add a lightweight web UI for reviewers and quant users.
- Add a downstream portfolio-construction protocol to separate signal quality from allocation quality.

## Links To Fill Before Submission

- Code repository: to be filled.
- Demo video: to be filled.
- Testing instructions: `REVIEWER_INSTRUCTIONS.md`.
- Architecture: `ARCHITECTURE.md`.
- Demo script: `DEMO_SCRIPT.md`.
- ADK Web guide: `ADK_WEB_DEMO.md`.
- Deployment notes: `DEPLOYMENT.md`.
