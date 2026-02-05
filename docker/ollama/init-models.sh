#!/bin/bash
# =============================================================================
# Ollama Models Initialization Script
# =============================================================================
# Downloads required models for the specialized AI agents.
# This script runs in the background after Ollama starts.
#
# Models:
# - llama3.1:8b - Financial control and personal planning agents
# - mistral:7b - Security and reading agents
# =============================================================================

set -e

echo "[init-models] Starting Ollama models download..."

# Wait for Ollama to be ready
MAX_RETRIES=30
RETRY_COUNT=0

while ! ollama list > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "[init-models] ERROR: Ollama not ready after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "[init-models] Waiting for Ollama to be ready... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "[init-models] Ollama is ready. Checking required models..."

# Function to pull model if not exists
pull_if_missing() {
    local model=$1
    if ollama list | grep -q "^$model"; then
        echo "[init-models] Model $model already exists, skipping..."
    else
        echo "[init-models] Downloading model $model..."
        ollama pull "$model"
        echo "[init-models] Model $model downloaded successfully."
    fi
}

# Pull required models
pull_if_missing "llama3.1:8b"
pull_if_missing "mistral:7b"

echo "[init-models] All required models are ready!"
echo "[init-models] Available models:"
ollama list
