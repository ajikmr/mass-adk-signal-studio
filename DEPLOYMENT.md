# MASS-ADK Deployment Notes

This document describes practical deployment and testing paths for MASS-ADK.

Current status:

- Local ADK execution is validated.
- ADK Web execution is supported.
- Local stdio MCP execution is validated.
- The integrated MASS engine runs a self-contained sample-backed smoke test locally.
- The artifact-store abstraction supports local storage and has a GCS-ready backend.
- A hosted Cloud Run or Agent Runtime deployment has not yet been finalized.

## Deployment Modes

| Mode | Status | Purpose |
| --- | --- | --- |
| Local ADK CLI | Validated | Fastest reviewer path and video demo path |
| ADK Web | Supported | Browser-based local demo |
| Local stdio MCP | Validated | Demonstrates secure read-only tool exposure |
| GCS artifact backend | Implemented, needs project-specific smoke test | Demonstrates Google Cloud artifact routing |
| Cloud Run | Planned | Containerized deployment path for ADK/MCP services |
| Agent Runtime | Planned | Managed Google Agent Platform deployment path |

## Prerequisites

Use the dedicated conda environment:

```bash
cd other_repo/MASS/adk_related/MASS_adk
conda env create -f environment.yml
conda activate mass-adk
cp .env.example .env
```

If the environment already exists:

```bash
conda activate mass-adk
pip install -e ".[eval]"
```

Configure Google authentication:

```bash
gcloud auth login
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

Enable core APIs if needed:

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

Recommended `.env` values:

```bash
MASS_ADK_MODEL=gemini-3.5-flash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=global
GOOGLE_CLOUD_STORAGE_BUCKET=YOUR_BUCKET_NAME
MASS_ADK_DEPLOY_REGION=us-central1

MASS_ADK_ENABLE_LIVE_RUNS=false
MASS_ADK_ARTIFACT_BACKEND=local
MASS_ADK_LOCAL_ARTIFACT_ROOT=./artifacts
MASS_ADK_GCS_PREFIX=mass-adk
```

Optional copied-engine live smoke variables:

```bash
MASS_MODEL_NAME=your-openai-compatible-model
MASS_MODEL_SERVER=https://your-openai-compatible-endpoint.example.com/v1
MASS_API_KEY=your-openai-compatible-api-key
```

Do not commit `.env` or credentials.

## Mode 1: Local ADK CLI

Run the main MASS-ADK agent:

```bash
adk run mass_adk "List the completed MASS experiments available in this demo and identify which are multi-seed versus single-seed."
```

Run the ADK-native investor-decision adapter:

```bash
adk run mass_engine_adk "Use the demo investor decision case, select two synthetic stocks, validate the decision, and return the final JSON."
```

Run the MCP-client ADK agent:

```bash
adk run mass_adk_mcp "List MASS experiments through MCP and explain the evidence caveats."
```

## Mode 2: ADK Web

Start ADK Web locally:

```bash
bash scripts/launch_adk_web_demo.sh
```

This wraps:

```bash
adk web . --host 127.0.0.1 --port 8501 --no-reload
```

Then select one of these agents in the browser:

```text
mass_adk
mass_engine_adk
mass_adk_mcp
```

Recommended browser demo prompts:

```text
List the completed MASS experiments available in this demo and identify which are multi-seed versus single-seed.
```

```text
Inspect integrated MASS-ADK result artifacts and explain how they connect the ADK app to the sample-backed engine smoke run.
```

```text
Which stocks should I buy based on the MASS results?
```

## Mode 3: Self-Contained Engine Smoke Test

Dry-run mode writes manifest and progress records without live LLM calls:

```bash
python -m mass_engine.runner --smoke
```

Expected result:

```text
status: dry_run
executed: false
```

Live sample-backed smoke execution is guarded and intentionally explicit:

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

This uses bundled synthetic sample data. It verifies execution plumbing only and does not reproduce paper-scale empirical findings.

Generated local artifacts:

```text
artifacts/runs/<run_id>/manifest.json
artifacts/runs/<run_id>/progress.json
artifacts/mass_engine/results/<run_id>.parq
artifacts/mass_engine/results/dist_<run_id>_5_positive.pkl
artifacts/mass_engine/results/checkpoints/<run_id>/
```

## Mode 4: Local MCP Server

List exposed MCP tools:

```bash
python -m mass_adk.mcp_server --list-tools
```

The MCP server exposes read-only tools such as:

```text
list_available_experiments
compare_experiments
validate_mass_runtime_paths
list_mass_result_artifacts
list_mass_checkpoints
inspect_mass_checkpoint
list_mass_engine_runs
inspect_mass_engine_run
```

It intentionally excludes live-run tools.

## Mode 5: Optional GCS Artifact Backend Smoke

The artifact-store abstraction supports GCS. A dry-run GCS smoke can validate cloud artifact routing without live LLM calls.

Set `.env` or shell variables:

```bash
MASS_ADK_ARTIFACT_BACKEND=gcs
GOOGLE_CLOUD_STORAGE_BUCKET=YOUR_BUCKET_NAME
MASS_ADK_GCS_PREFIX=mass-adk
```

Run:

```bash
MASS_ADK_ARTIFACT_BACKEND=gcs python -m mass_engine.runner --smoke
```

Expected cloud artifacts:

```text
gs://YOUR_BUCKET_NAME/mass-adk/runs/<run_id>/manifest.json
gs://YOUR_BUCKET_NAME/mass-adk/runs/<run_id>/progress.json
```

This path is useful for demonstrating Google Cloud artifact storage. It does not require `MASS_ADK_ENABLE_LIVE_RUNS=true` unless you also want to execute the live engine smoke run.

## Cloud Run Roadmap

Cloud Run is the recommended lightweight hosted path for the ADK/MCP service layer.

Suggested architecture:

```text
Cloud Run service: MASS-ADK ADK app or lightweight API wrapper
Cloud Run service or sidecar: read-only MCP server
GCS bucket: run manifests, progress records, checkpoints, result artifacts
Vertex AI: Gemini model serving
```

Recommended constraints:

- Keep live engine execution disabled by default.
- Expose read-only artifact and experiment inspection first.
- Use Secret Manager for API keys and `.env`-style secrets.
- Use GCS for artifact storage rather than container-local disk.
- Run expensive simulations as separate jobs, not interactive requests.

Minimal future Cloud Run steps:

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT_ID/REPO/mass-adk:latest
gcloud run deploy mass-adk \
  --image REGION-docker.pkg.dev/PROJECT_ID/REPO/mass-adk:latest \
  --region us-central1 \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_LOCATION=global,MASS_ADK_ARTIFACT_BACKEND=gcs,MASS_ADK_GCS_PREFIX=mass-adk
```

This roadmap is intentionally documented as future deployment work unless a container image and hosted endpoint are validated.

## Agent Runtime Roadmap

Agent Runtime is the natural managed deployment target for the ADK agent layer.

Recommended future path:

1. Keep `mass_adk` as the primary deployed agent.
2. Keep `mass_engine_adk` as a secondary demo agent.
3. Keep `mass_adk_mcp` for explicit MCP-client demonstration.
4. Store run artifacts in GCS.
5. Use Agent Runtime sessions/memory only for user interaction state, not for large simulation artifacts.

## Validation Checklist

Run these before recording or submitting:

```bash
python -m pytest -q
python -m mass_engine.runner --smoke
python -m mass_adk.mcp_server --list-tools
adk run mass_adk "Validate the self-contained MASS-ADK smoke setup and confirm whether reviewers need the original MASS dataset."
adk run mass_engine_adk "Use the demo investor decision case, select two synthetic stocks, validate the decision, and return the final JSON."
adk eval mass_adk eval/data/mass_adk_safety.test.json --config_file_path eval/safety_eval_config.json
```

Expected baseline:

```text
28 passed
MCP tool list includes read-only tools
sample_data/ih_smoke is used for smoke tests
no buy/sell recommendation in safety prompt
```

## Limitations

- Hosted Cloud Run and Agent Runtime deployments are roadmap items unless explicitly validated.
- GCS artifact storage is implemented but should be smoke-tested in the target project before claiming production deployment.
- Bundled sample data is synthetic and validates execution plumbing only.
- Paper-scale empirical reproduction requires original research data and expensive multi-seed runs.
