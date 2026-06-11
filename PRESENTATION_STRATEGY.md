# Presentation Strategy

This document summarizes lessons from the official challenge guide and the reviewed past submissions, then maps them to how MASS-ADK should be presented.

## What Past Submissions Do Well

| Pattern | Examples Observed | MASS-ADK Implication |
| --- | --- | --- |
| Strong one-line product identity | EnergyAgentAI and SalesShortcut state the business workflow immediately | Lead with “auditable financial signal research workflow,” not internal repo details |
| Visual architecture early | EnergyAgentAI, SalesShortcut, BleachAgentBuilder include diagrams near the top | Put `ARCHITECTURE.md` and an exported diagram in the final submission |
| Concrete business scenario | SalesShortcut starts from a real manual sales process | Start from quant teams manually interpreting expensive LLM-agent experiments |
| Clear “what it does” | Past submissions list end-user capabilities, not only tech stack | Emphasize inspect, compare, explain, evaluate, and govern MASS experiments |
| Google stack clearly named | ADK, Gemini, Cloud Run, BigQuery, Vertex are explicit | Name ADK, Gemini via Vertex, ADK eval, MCP, and future Cloud Run/Agent Runtime |
| Detailed quick start | TradeSage and EnergyAgentAI provide commands and prerequisites | Use `REVIEWER_INSTRUCTIONS.md` as the reviewer entry point |
| Demo-friendly commands | SalesShortcut gives direct local/cloud run options | Keep the demo deterministic: cached evidence, checkpoint inspection, MCP, safety prompt |
| Hackathon story | SalesShortcut has inspiration, challenges, accomplishments, next steps | Use `DEVPOST_SUBMISSION_DRAFT.md` for the final submission narrative |

## Official Guide Requirements

The official guide emphasizes four required assets:

| Requirement | MASS-ADK Asset |
| --- | --- |
| Code | `MASS_adk/` package with ADK agents, tools, MCP server, tests |
| Video | `DEMO_SCRIPT.md` |
| Architecture diagram | `ARCHITECTURE.md`; export Mermaid to PNG/SVG before submission |
| Testing access | `REVIEWER_INSTRUCTIONS.md` |

The guide also emphasizes Track 2 optimization themes:

- stress-test reasoning,
- evaluate edge cases,
- debug stalled logic,
- refine instructions,
- show production-grade reliability,
- highlight before vs after.

## Recommended Positioning

Use this framing:

```text
MASS-ADK Signal Studio is a Track 2 optimization project. We took MASS, an existing multi-agent financial signal research system, and hardened it with Google ADK, Gemini, ADK eval, MCP, artifact inspection, and finance-safety guardrails.
```

Avoid this framing:

```text
An AI trading bot that finds profitable stocks.
```

The latter creates regulatory risk and misrepresents the system.

## Best Opening For Video

Use a simple before/after setup:

```text
Before MASS-ADK, MASS was a powerful research engine, but interpreting runs required manually reading result files, checkpoint folders, and experiment notes. It was hard to show reliability, safety, and evidence quality to a reviewer or business user.

After MASS-ADK, the same MASS engine is wrapped in a Google ADK and Gemini control layer. The agent can inspect cached evidence, read checkpoint state, expose safe tools through MCP, run ADK evals, and produce research-only summaries that do not become investment advice.
```

## What To Show In The Demo

Recommended sequence:

1. Architecture diagram from `ARCHITECTURE.md`.
2. ADK Web launch with MASS-ADK branding.
3. Unit tests passing.
4. Cached experiment inventory in `mass_adk`.
5. China 512-agent mechanism comparison.
6. Integrated sample-backed artifact/checkpoint inspection.
7. Integrated after-version `mass_engine.runner --smoke` dry-run or live smoke output.
8. ADK-native investor decision adapter using synthetic data.
9. MCP server tool list and MCP-client prompt.
10. Safety prompt refusing stock recommendations.
11. ADK eval summary.

This sequence maps directly to the judging criteria:

| Judging criterion | Demo moment |
| --- | --- |
| Technical implementation | ADK agents, MCP, artifact tools, evals |
| Business case | Quant workflow and human-reviewed signal research |
| Innovation | Multi-agent disagreement signal governance |
| Demo/presentation | Deterministic command-driven walkthrough |

## What To Avoid In The Demo

- Do not run a long MASS simulation live.
- Do not over-explain the original MASS paper.
- Do not claim portfolio returns from Rank IC.
- Do not recommend securities.
- Do not spend time on conda setup unless the reviewer specifically asks.
- Do not show raw huge logs unless necessary.

## Submission Page Copy

Suggested short description:

```text
MASS-ADK Signal Studio turns an existing multi-agent financial signal research engine into a Google ADK and Gemini-powered research workflow. It inspects cached experiments and original MASS checkpoints, compares signal mechanisms, exposes read-only tools through MCP, runs ADK evals, and enforces finance-safety guardrails so quant teams can audit LLM-derived market signals before downstream portfolio construction.
```

Suggested “built with” list:

```text
Google ADK, Gemini 3.5 Flash via Vertex AI, ADK Eval, MCP, Python, Conda, SQLite, Parquet artifacts, Google Cloud authentication, future Cloud Run / Agent Runtime deployment path.
```

Suggested tagline:

```text
From multi-agent finance prototype to auditable ADK/Gemini signal research workflow.
```

## Visual Assets To Produce

Exported architecture assets are available under `assets/`:

```text
assets/architecture.png
assets/native_adk_flow.png
assets/mcp_flow.png
```

Before final submission, also capture:

1. Terminal screenshot of `python -m pytest -q` showing 28 tests pass.
2. Browser screenshot of ADK Web with the `mass_adk`, `mass_engine_adk`, and `mass_adk_mcp` agents visible.
3. Terminal screenshot of `python -m mass_adk.mcp_server --list-tools`.
4. Terminal screenshot of `python -m mass_engine.runner --smoke` showing dry-run manifest/progress URIs.
5. ADK Web screenshot of experiment inventory response.
6. ADK Web screenshot of finance-safety refusal.

## Final Submission Checklist

- `README.md` gives quick setup.
- `SUBMISSION.md` explains project, business case, and evidence.
- `DEVPOST_SUBMISSION_DRAFT.md` provides copy for submission form.
- `ARCHITECTURE.md` provides diagrams.
- `DEMO_SCRIPT.md` supports recording.
- `ADK_WEB_DEMO.md` provides ADK Web prompt cards.
- `DEPLOYMENT.md` documents local, GCS, Cloud Run, and Agent Runtime paths.
- `REVIEWER_INSTRUCTIONS.md` gives commands and pass criteria.
- Demo video recorded.
- Architecture images exported under `assets/`.
- Testing access instructions included.
- No credentials or service-account JSON files committed.
