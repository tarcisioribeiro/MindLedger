# =============================================================================
# Embeddings Service - Dockerfile
# =============================================================================
# Serviço independente de geração de embeddings usando sentence-transformers.
# Projetado para ser reutilizável por múltiplos projetos.
#
# Decisões arquiteturais:
# - Modelo pré-baixado no build para evitar download em runtime
# - Cache persistente via volumes para HF_HOME
# - Multi-stage build para imagem final menor (opcional em futuras versões)
# - CPU-only (sem dependências CUDA) para simplicidade e portabilidade
# =============================================================================

FROM python:3.12-slim

# Metadados do container
LABEL maintainer="PersonalHub Team"
LABEL description="Embedding generation service using sentence-transformers"
LABEL version="1.0.0"

WORKDIR /app

# Variáveis de ambiente para cache de modelos Hugging Face
# Essas variáveis garantem que o modelo seja baixado para um local persistente
ENV HF_HOME=/app/models
ENV TRANSFORMERS_CACHE=/app/models
ENV SENTENCE_TRANSFORMERS_HOME=/app/models
ENV PYTHONUNBUFFERED=1

# Instalar dependências do sistema mínimas
# - curl: healthcheck
# - Sem build-essential pois sentence-transformers tem wheels pré-compilados
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (otimização de cache de camadas)
COPY requirements.txt .

# Instalar dependências Python
# --no-cache-dir economiza espaço na imagem final
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Criar diretório para modelos com permissões corretas
RUN mkdir -p /app/models && chmod 755 /app/models

# PRÉ-DOWNLOAD DO MODELO durante o build
# Isso evita download em runtime e torna o startup instantâneo
# O modelo all-MiniLM-L6-v2 tem ~80MB
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
print('Downloading model all-MiniLM-L6-v2...'); \
model = SentenceTransformer('all-MiniLM-L6-v2'); \
print('Model downloaded successfully to /app/models'); \
print(f'Model info: {model.get_sentence_embedding_dimension()} dimensions')"

# Copiar código da aplicação
COPY app.py .

# Criar usuário não-root para segurança
RUN useradd -m -u 1000 embeddings && \
    chown -R embeddings:embeddings /app

USER embeddings

# Porta padrão do serviço
EXPOSE 8080

# Healthcheck para monitoramento
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando de inicialização
# --host 0.0.0.0 permite conexões de outros containers
# --workers 1 é suficiente para CPU-only (evita competição por recursos)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
