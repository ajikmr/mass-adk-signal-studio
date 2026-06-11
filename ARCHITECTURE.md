# MASS-ADK Architecture

## Overview

MASS-ADK is a productionization layer around the original MASS multi-agent financial signal research engine.

Original MASS remains responsible for expensive investor-agent simulations and artifact generation. MASS-ADK provides Google ADK orchestration, Gemini-powered analysis, read-only artifact tools, ADK evals, MCP integration, and finance-safety reporting.

## High-Level Architecture

Rendered image:

![MASS-ADK Architecture](assets/architecture.png)

Mermaid source:

```mermaid
flowchart TD
    User[Reviewer / Quant Researcher] --> ADK[ADK Root Agent\nmass_adk_signal_studio]

    ADK --> Gemini[Gemini via Vertex AI\nMASS_ADK_MODEL]
    ADK --> Tools[Native ADK Function Tools]
    ADK --> Subagents[Specialist ADK Subagents]

    Subagents --> DataAgent[Data Analyst]
    Subagents --> SignalAgent[Signal Analyst]
    Subagents --> OptimizerAgent[Optimizer Analyst]
    Subagents --> EvalAgent[Evaluation Analyst]
    Subagents --> ComplianceAgent[Compliance Reviewer]

    Tools --> Manifest[Curated Experiment Manifest\nexperiment_manifest.json]
    Tools --> ArtifactTools[Read-Only Artifact Tools]
    Tools --> ReportTools[Research Memo Tools]

    ArtifactTools --> Results[MASS Result Artifacts\n.parq / .pkl filenames]
    ArtifactTools --> Checkpoints[MASS Checkpoint Folders\nmanifest.json / progress.json / SQLite]

    MASS[Original MASS Runtime\nstock_disagreement/main.py] --> Results
    MASS --> Checkpoints
    MASS --> Datasets[China ih and SP500 datasets]

    Engine[Integrated After-Version MASS Engine\nmass_engine.runner] --> Store[Artifact Store\nlocal or GCS-ready]
    Store --> EngineRuns[Run Manifests / Progress\nartifacts/runs]
    Tools --> EngineRuns

    InvestorAdapter[ADK-Native Investor Decision Adapter\nmass_engine_adk] --> Gemini
    InvestorAdapter --> AdapterTools[Synthetic Case + Decision Validator]

    MCPServer[MASS-ADK Read-Only MCP Server\nmass_adk.mcp_server] --> Manifest
    MCPServer --> ArtifactTools

    MCPAgent[Optional ADK MCP Client\nmass_adk_mcp] --> MCPToolset[ADK McpToolset]
    MCPToolset --> MCPServer
    MCPAgent --> Gemini

    Eval[ADK Eval Suites\nresearch / artifact / safety] --> ADK
```

## Runtime Boundary

| Layer | Environment | Main responsibility |
| --- | --- | --- |
| Original MASS | `twinmarket` | Live/offline simulations, checkpoints, signal artifacts |
| Integrated MASS engine | `mass-adk` | After-version dry-run manifests, guarded smoke execution, local/GCS-ready artifact routing |
| ADK investor adapter | `mass-adk` | Synthetic one-step investor decision demo using ADK tools and structured JSON |
| MASS-ADK | `mass-adk` | ADK/Gemini analysis, read-only inspection, evals, MCP, demo UX |

This separation keeps the original research engine stable while allowing the ADK layer to be iterated quickly for competition and productionization work.

## Native ADK Flow

Rendered image:

![Native ADK Flow](assets/native_adk_flow.png)

Mermaid source:

```mermaid
sequenceDiagram
    participant U as User
    participant A as mass_adk Agent
    participant G as Gemini
    participant T as ADK Tools
    participant M as MASS Artifacts

    U->>A: Ask for experiment summary or artifact inspection
    A->>G: Interpret request and choose tools
    A->>T: Call list/compare/inspect tools
    T->>M: Read manifest, result filenames, checkpoint JSON, SQLite counts
    M-->>T: Return read-only metadata
    T-->>A: Tool response
    A->>G: Compose grounded explanation with caveats
    A-->>U: Research-only answer, no investment advice
```

## MCP Flow

Rendered image:

![MCP Flow](assets/mcp_flow.png)

Mermaid source:

```mermaid
sequenceDiagram
    participant U as User
    participant C as mass_adk_mcp Agent
    participant S as ADK McpToolset
    participant M as MASS-ADK MCP Server
    participant R as Read-Only Tools

    U->>C: Ask via MCP-client agent
    C->>S: Select MCP tool
    S->>M: stdio MCP call_tool
    M->>R: Execute read-only function
    R-->>M: JSON result
    M-->>S: MCP TextContent JSON
    S-->>C: Tool response
    C-->>U: Gemini-generated explanation with caveats
```

## Data And Artifact Sources

MASS-ADK currently uses two evidence sources.

Curated cached evidence:

```text
mass_adk/data/experiment_manifest.json
```

Original MASS runtime artifacts:

```text
other_repo/MASS/stock_disagreement/res/
other_repo/MASS/stock_disagreement/res/checkpoints/
```

The artifact tools are read-only. They inspect:

- configured MASS paths,
- result filenames and sizes,
- checkpoint `manifest.json`,
- checkpoint `progress.json`,
- per-date shard counts,
- SQLite table names and row counts.

They do not currently parse parquet or pickle contents.

Integrated after-version run metadata:

```text
MASS_adk/artifacts/runs/<run_id>/manifest.json
MASS_adk/artifacts/runs/<run_id>/progress.json
```

The integrated `mass_engine.runner --smoke` path defaults to dry-run metadata creation. Live execution is guarded by `MASS_ADK_ENABLE_LIVE_RUNS=true`.

## Safety Controls

Safety controls are implemented through prompts, tool boundaries, and evals.

| Control | Implementation |
| --- | --- |
| No trading recommendations | Root and specialist prompts |
| Research-only framing | Root, compliance, and MCP-client prompts |
| Signal vs return distinction | Prompts and eval rubrics |
| Single-seed caveats | Manifest, prompts, eval rubrics |
| No expensive default live runs | `run_smoke_experiment` disabled and excluded from MCP |
| Read-only MCP tools | MCP server exposes inspection tools only |
| Guarded integrated engine | `mass_engine.runner --smoke` defaults to dry-run records |

## Deployment Path

Current state is local development and review.

Recommended production path:

1. Deploy MASS-ADK as an ADK app or Cloud Run service.
2. Keep MCP read-only tools as a sidecar or separate Cloud Run service.
3. Store MASS artifacts in GCS or a controlled artifact store.
4. Run large MASS simulations as offline jobs, Cloud Run Jobs, or batch jobs.
5. Let MASS-ADK inspect artifacts after completion instead of launching expensive runs interactively.

## Competition-Relevant Capabilities

| Criterion | Architecture support |
| --- | --- |
| Technical implementation | ADK agents, tools, MCP server, MCP client, evals, artifact inspection |
| Business case | Quant research workflow for evaluating LLM-derived financial signals |
| Innovation | Multi-agent disagreement signal research plus ADK productionization |
| Demo and presentation | Deterministic cached evidence, real local artifacts, safety prompt, evals |
