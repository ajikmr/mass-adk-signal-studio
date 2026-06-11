# MASS Engine Integration Plan

## Goal

Create a competition-integrated copy of the original MASS runtime inside `MASS_adk` so the project has a clear before/after story.

Before:

```text
other_repo/MASS/
```

Original MASS research prototype. It runs simulations and writes local result/checkpoint artifacts.

After:

```text
other_repo/MASS/adk_related/MASS_adk/
```

Google ADK/Gemini/MCP-integrated MASS package. It contains the ADK app plus an adapted MASS engine that can run against bundled synthetic smoke data and write artifacts through a local or Google Cloud Storage-ready backend.

## Recommended Package Boundary

Do not copy original MASS directly into `mass_adk/`. Keep the ADK control layer and MASS runtime layer separate.

Target layout:

```text
MASS_adk/
  mass_adk/                  # ADK/Gemini/MCP control layer
    agent.py
    tools/
    sub_agents/
    mcp_server.py

  mass_engine/               # Adapted copy of original MASS runtime
    __init__.py
    runner.py
    stock_disagreement/
    cloud/
      __init__.py
      artifact_store.py
      local_store.py
      gcs_store.py

  sample_data/               # Tiny synthetic smoke datasets for reviewers
    ih_smoke/
    sp500_smoke/

  mass_engine_adk/            # Thin ADK-native adapter for one investor decision step
    agent.py
    prompts.py
    tools.py

  tests/
  eval/
  README.md
  SUBMISSION.md
```

Rationale:

- `mass_adk` remains the agent/control layer.
- `mass_engine` becomes the packaged MASS runtime.
- `sample_data` makes smoke testing self-contained without original MASS datasets.
- `mass_engine_adk` demonstrates an ADK-native MASS-style investor decision without rewriting the full engine.
- Original `other_repo/MASS/` remains untouched as the before version.
- Competition reviewers can see the after version as a single integrated package.

## Copy Scope

Copy into `mass_engine/`:

```text
other_repo/MASS/stock_disagreement/
```

Do not copy:

- `adk_related/`
- original datasets
- large result outputs under `stock_disagreement/res/`
- old paper notes
- notebooks unless required for runtime
- credentials or `.env` files

The integrated package now includes tiny synthetic smoke datasets so reviewers do not need the full research dataset.

```bash
MASS_ADK_DATASET_ROOT=./sample_data/ih_smoke
MASS_ADK_SP500_DATA_ROOT=./sample_data/sp500_smoke
```

These files are only for smoke testing and operational verification. They are not research data and must not be used for financial conclusions.

Generic macro filenames are used in every smoke dataset:

```text
macro_data/policy_rate.csv
macro_data/cpi_yoy.csv
macro_data/equity_index_pe_ttm.csv
macro_data/market_sentiment.csv
macro_data/ten_year_government_bond_yield.csv
```

Country-specific filenames were intentionally removed so `ih_smoke` and `sp500_smoke` share one formal schema.

## Artifact Store Abstraction

Add a small artifact-store interface used by the adapted MASS runtime.

Conceptual API:

```python
class ArtifactStore:
    def write_json(self, path: str, payload: dict) -> str: ...
    def read_json(self, path: str) -> dict: ...
    def write_bytes(self, path: str, payload: bytes) -> str: ...
    def read_bytes(self, path: str) -> bytes: ...
    def exists(self, path: str) -> bool: ...
    def list(self, prefix: str) -> list[str]: ...
```

Backends:

```text
LocalArtifactStore
GCSArtifactStore
```

Environment configuration:

```bash
MASS_ADK_ARTIFACT_BACKEND=local
# or
MASS_ADK_ARTIFACT_BACKEND=gcs

GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name
MASS_ADK_GCS_PREFIX=mass-adk
MASS_ADK_LOCAL_ARTIFACT_ROOT=./artifacts
```

## Cloud Artifact Layout

Use deterministic run-scoped artifact paths.

```text
gs://<bucket>/<prefix>/runs/<run_id>/
  manifest.json
  progress.json
  logs/
    run.log
  checkpoints/
    date_signals/
    date_optimizer/
    agent_state/
    snapshots/
    agent_results.sqlite
  final/
    signal_result.parq
    distribution.pkl
```

Equivalent local layout:

```text
artifacts/runs/<run_id>/
  manifest.json
  progress.json
  logs/
  checkpoints/
  final/
```

## Run Manifest

Every adapted MASS run should write a `manifest.json` containing:

- run id,
- timestamp,
- MASS-ADK version,
- ADK model name,
- engine model name,
- project id,
- model-serving location,
- artifact backend,
- bucket and prefix if using GCS,
- stock pool,
- date range,
- seed,
- agent count,
- optimizer,
- signal objective,
- learn-alpha flag,
- turnover penalty,
- smoke/full run flag.

This makes later ADK inspection deterministic and auditable.

## Execution Policy

Default behavior must remain safe.

- Large 64-agent and 512-agent runs should not be launched by default.
- ADK should not trigger expensive runs unless explicitly enabled.
- Smoke runs should remain tiny and bounded.

Environment guard:

```bash
MASS_ADK_ENABLE_LIVE_RUNS=false
```

Optional smoke command target:

```bash
python -m mass_engine.runner --smoke --stock_pool ih --artifact_backend local
```

Current default behavior is dry-run metadata creation. Add `--execute` only for guarded live smoke execution.

Validated live smoke command:

```bash
MASS_ADK_ENABLE_LIVE_RUNS=true python -m mass_engine.runner --smoke --execute
```

Expected result:

```text
status: completed
executed: true
returncode: 0
dataset_root: sample_data/ih_smoke
```

Later GCS smoke command:

```bash
MASS_ADK_ARTIFACT_BACKEND=gcs \
python -m mass_engine.runner --smoke --stock_pool ih
```

## ADK Tool Integration

Existing tools inspect self-contained MASS-ADK artifacts. They inspect the configured artifact store for integrated after-version run records and the copied-engine result/checkpoint outputs under `artifacts/mass_engine/results`.

Integrated tools:

```text
list_mass_engine_runs
inspect_mass_engine_run
```

Future tools:

```text
list_cloud_mass_runs
inspect_cloud_mass_run
compare_before_after_artifact_layout
```

MCP exposure should remain read-only:

- expose run listing,
- expose checkpoint inspection,
- expose manifest inspection,
- do not expose expensive live-run tools.

## Implementation Phases

### Phase 1: Engine Snapshot

- [x] Copy required original MASS runtime code into `mass_engine/`.
- [x] Exclude old result artifacts, datasets, and credentials.
- [x] Add `mass_engine/__init__.py`.
- [x] Add a minimal `mass_engine/runner.py` wrapper.
- [x] Ensure the smoke command can be represented through the wrapper with dry-run local output.
- [x] Add bundled synthetic sample data under `sample_data/`.
- [x] Switch copied-engine defaults to sample data rather than original MASS datasets.

Success criteria:

```bash
conda activate mass-adk
python -m mass_engine.runner --smoke --stock_pool ih
```

produces a dry-run command preview plus local manifest/progress records using bundled sample data.

### Phase 2: Local Artifact Store

- [x] Add `LocalArtifactStore`.
- [x] Write `manifest.json` and `progress.json` through the store.
- [x] Keep live execution guarded until the adapter is stable.
- [x] Add tests for artifact-store path safety and manifest writes.
- [x] Validate guarded live sample-backed smoke execution end-to-end.
- [x] Route copied-engine result and checkpoint outputs under `artifacts/mass_engine/results`.

Success criteria:

```text
artifacts/runs/<run_id>/manifest.json
artifacts/runs/<run_id>/progress.json
```

exist after a smoke run or simulated run.

### Phase 3: GCS Artifact Store

- [x] Add `GCSArtifactStore` using Google Cloud Storage client libraries.
- [ ] Upload manifest/progress/logs first in a real GCS smoke test.
- Upload final result artifacts after local behavior is stable.
- Keep local fallback.

Success criteria:

```bash
MASS_ADK_ARTIFACT_BACKEND=gcs python -m mass_engine.runner --smoke --stock_pool ih
```

writes a run manifest under:

```text
gs://<bucket>/mass-adk/runs/<run_id>/manifest.json
```

### Phase 4: ADK Inspection Tools

- [x] Add ADK tools that read from local or GCS artifact stores.
- [ ] Add eval cases for cloud-backed run inspection.
- [x] Add MCP exposure for read-only integrated engine artifact inspection.
- [x] Validate ADK inspection of completed sample-backed integrated run.

Success criteria:

```bash
adk run mass_adk "Inspect the latest MASS engine run and summarize its artifact backend and checkpoint state."
```

returns a grounded answer from artifact-store metadata.

### Phase 5: Submission Update

- Update `SUBMISSION.md`.
- Update `ARCHITECTURE.md`.
- Update `DEMO_SCRIPT.md`.
- Update `DEVPOST_SUBMISSION_DRAFT.md`.
- Record demo showing before vs after.

## Competition Story

Before:

```text
MASS was a local research prototype with powerful multi-agent finance experiments, but result inspection, checkpoint interpretation, and safety behavior were manual and local-file oriented.
```

After:

```text
MASS-ADK packages the MASS engine inside a Google ADK project, routes analysis through Gemini, exposes read-only inspection through MCP, evaluates behavior with ADK eval, and supports cloud-backed artifact storage through GCS.
```

For reviewer execution, MASS-ADK also includes bundled synthetic smoke datasets so the after-version can be run end-to-end without sharing the full research dataset.

This strengthens the Track 2 claim: the existing agentic finance system was optimized for reliability, auditability, and production-style operation.

## Risks And Constraints

- Copying too much original MASS code may make the package large and harder to review.
- Refactoring all file writes to GCS may take longer than the competition timeline allows.
- GCS-backed parquet/pickle writes should be added after manifest/progress writes are stable.
- Keep original MASS untouched to avoid breaking prior research results.
- Do not overclaim full production deployment until Cloud Run or Agent Runtime is actually tested.
- Do not present smoke-data metrics as research evidence; they only validate execution plumbing.

## Initial Recommendation

Phase 1 and Phase 2 are complete, including live sample-backed smoke validation. Next optional work is Phase 3 real GCS smoke testing and Cloud Run / Agent Runtime deployment notes. These are useful but not required for the local reviewer path.
