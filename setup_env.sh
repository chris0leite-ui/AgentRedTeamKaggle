#!/usr/bin/env bash
# Re-provision the ephemeral container for local development / scoring.
# Kaggle credentials (KAGGLE_USERNAME / KAGGLE_KEY) are provided via the environment.
set -euo pipefail
cd "$(dirname "$0")"

pip install --quiet kaggle pydantic gymnasium
export KAGGLE_API_TOKEN="${KAGGLE_KEY:?KAGGLE_KEY not set}"

if [ ! -d sdk/aicomp_sdk ]; then
  mkdir -p sdk
  ( cd sdk
    kaggle competitions download -c ai-agent-security-multi-step-tool-attacks -p .
    unzip -o -q ./*.zip )
fi
echo "Setup complete. SDK source at sdk/aicomp_sdk (deterministic agent needs no torch)."
