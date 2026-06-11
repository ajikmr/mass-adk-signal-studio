FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    GOOGLE_GENAI_USE_VERTEXAI=true \
    GOOGLE_CLOUD_LOCATION=global \
    MASS_ADK_MODEL=gemini-3.5-flash \
    MASS_ADK_ENABLE_LIVE_RUNS=false \
    MASS_ADK_ARTIFACT_BACKEND=local \
    MASS_ADK_LOCAL_ARTIFACT_ROOT=/tmp/mass-adk-artifacts \
    MASS_ADK_RESULTS_ROOT=/tmp/mass-adk-results

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY mass_adk ./mass_adk
COPY mass_adk_mcp ./mass_adk_mcp
COPY mass_engine ./mass_engine
COPY mass_engine_adk ./mass_engine_adk
COPY sample_data ./sample_data
COPY eval ./eval
COPY assets ./assets
COPY scripts ./scripts

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

RUN chmod +x scripts/start_adk_web_cloud_run.sh

CMD ["bash", "scripts/start_adk_web_cloud_run.sh"]
