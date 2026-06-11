#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${APP_DIR}"

PORT="${MASS_ADK_WEB_PORT:-8501}"
HOST="${MASS_ADK_WEB_HOST:-127.0.0.1}"

echo "Starting MASS-ADK ADK Web demo"
echo "App directory: ${APP_DIR}"
echo "URL: http://${HOST}:${PORT}"
echo
echo "Available agents in the ADK Web dropdown:"
echo "  - mass_adk"
echo "  - mass_engine_adk"
echo "  - mass_adk_mcp"
echo

exec adk web . \
  --host "${HOST}" \
  --port "${PORT}" \
  --no-reload \
  --log_level info
