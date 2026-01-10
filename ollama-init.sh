#!/bin/bash
# Script de inicializacao do Ollama - Baixa os modelos necessarios

set -e

OLLAMA_HOST="${OLLAMA_HOST:-localhost}"
OLLAMA_PORT="${OLLAMA_PORT:-11435}"
OLLAMA_URL="http://${OLLAMA_HOST}:${OLLAMA_PORT}"

# Modelos necessarios
EMBED_MODEL="${OLLAMA_EMBED_MODEL:-nomic-embed-text}"
LLM_MODEL="${OLLAMA_LLM_MODEL:-mistral:7b}"

echo "=== Ollama Model Initializer ==="
echo "Ollama URL: ${OLLAMA_URL}"
echo "Embed Model: ${EMBED_MODEL}"
echo "LLM Model: ${LLM_MODEL}"
echo ""

# Funcao para verificar se Ollama esta pronto
wait_for_ollama() {
  echo "Aguardando Ollama ficar disponivel..."
  for i in {1..60}; do
    if curl -s "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
      echo "Ollama esta pronto!"
      return 0
    fi
    echo "Tentativa $i/60 - aguardando..."
    sleep 2
  done
  echo "ERRO: Ollama nao ficou disponivel apos 2 minutos"
  return 1
}

# Funcao para verificar se modelo existe
model_exists() {
  local model=$1
  local models=$(curl -s "${OLLAMA_URL}/api/tags" | grep -o '"name":"[^"]*"' | sed 's/"name":"//g' | sed 's/"//g')
  for m in $models; do
    if [[ "$m" == "$model" ]] || [[ "$m" == "${model}:"* ]] || [[ "$model" == "${m}:"* ]]; then
      return 0
    fi
  done
  return 1
}

# Funcao para baixar modelo
pull_model() {
  local model=$1
  echo ""
  echo ">>> Baixando modelo: ${model}"

  if model_exists "$model"; then
    echo "Modelo ${model} ja existe, pulando..."
    return 0
  fi

  echo "Iniciando download de ${model}..."
  curl -X POST "${OLLAMA_URL}/api/pull" -d "{\"name\": \"${model}\"}" --no-buffer 2>&1 | while read line; do
    # Exibe progresso se houver
    if echo "$line" | grep -q "status"; then
      status=$(echo "$line" | grep -o '"status":"[^"]*"' | sed 's/"status":"//g' | sed 's/"//g')
      echo "  Status: ${status}"
    fi
  done

  # Verifica se foi baixado
  if model_exists "$model"; then
    echo "Modelo ${model} baixado com sucesso!"
    return 0
  else
    echo "ERRO: Falha ao baixar modelo ${model}"
    return 1
  fi
}

# Execucao principal
main() {
  wait_for_ollama

  echo ""
  echo "=== Verificando e baixando modelos ==="

  # Baixar modelo de embeddings (obrigatorio)
  if ! pull_model "$EMBED_MODEL"; then
    echo "ERRO CRITICO: Nao foi possivel baixar o modelo de embeddings"
    exit 1
  fi

  # Baixar modelo de LLM (opcional, Groq pode ser usado como fallback)
  if ! pull_model "$LLM_MODEL"; then
    echo "AVISO: Modelo LLM nao baixado, Groq sera usado como fallback"
  fi

  echo ""
  echo "=== Modelos instalados ==="
  curl -s "${OLLAMA_URL}/api/tags" | grep -o '"name":"[^"]*"' | sed 's/"name":"//g' | sed 's/"//g' | while read m; do
    echo "  - $m"
  done

  echo ""
  echo "=== Inicializacao concluida ==="
}

main "$@"
