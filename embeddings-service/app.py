"""
=============================================================================
Embeddings Service - FastAPI Application
=============================================================================
Serviço HTTP para geração de embeddings usando sentence-transformers.

Este serviço é projetado como infraestrutura compartilhada, similar a um
banco de dados ou cache. Pode ser reutilizado por múltiplos projetos.

Características:
- Modelo pré-carregado no startup para respostas rápidas
- Suporte a batch processing para eficiência
- Normalização L2 para compatibilidade com cosine similarity
- Health check endpoint para monitoramento
- Logs estruturados para observabilidade

Uso:
    POST /embeddings
    {
        "texts": ["texto 1", "texto 2", ...]
    }

    Response:
    {
        "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...]],
        "model": "all-MiniLM-L6-v2",
        "dimensions": 384
    }
=============================================================================
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sentence_transformers import SentenceTransformer

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# Configurações
# =============================================================================

MODEL_NAME = "all-MiniLM-L6-v2"
DIMENSIONS = 384
MAX_BATCH_SIZE = 128  # Limite para evitar OOM em requisições muito grandes
MAX_TEXT_LENGTH = 10000  # Caracteres máximos por texto


# =============================================================================
# Modelos Pydantic (Request/Response)
# =============================================================================

class EmbeddingRequest(BaseModel):
    """
    Request para geração de embeddings.

    Attributes:
        texts: Lista de textos para gerar embeddings.
               Mínimo 1, máximo MAX_BATCH_SIZE textos.
    """
    texts: List[str] = Field(
        ...,
        min_length=1,
        max_length=MAX_BATCH_SIZE,
        description="Lista de textos para gerar embeddings"
    )

    @field_validator('texts')
    @classmethod
    def validate_texts(cls, texts: List[str]) -> List[str]:
        """Valida cada texto individualmente."""
        validated = []
        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Texto no índice {i} está vazio")
            if len(text) > MAX_TEXT_LENGTH:
                raise ValueError(
                    f"Texto no índice {i} excede o limite de {MAX_TEXT_LENGTH} caracteres"
                )
            validated.append(text.strip())
        return validated


class EmbeddingResponse(BaseModel):
    """
    Response com embeddings gerados.

    Attributes:
        embeddings: Lista de vetores de embedding (384 dimensões cada)
        model: Nome do modelo usado
        dimensions: Número de dimensões dos embeddings
    """
    embeddings: List[List[float]]
    model: str = MODEL_NAME
    dimensions: int = DIMENSIONS


class HealthResponse(BaseModel):
    """Response do health check."""
    status: str
    model: str
    dimensions: int
    model_loaded: bool


class ModelInfoResponse(BaseModel):
    """Informações detalhadas do modelo."""
    model_name: str
    dimensions: int
    max_batch_size: int
    max_text_length: int
    is_local: bool = True
    supports_multilingual: bool = True


# =============================================================================
# Estado Global do Modelo
# =============================================================================

class ModelState:
    """
    Gerencia o estado do modelo de embeddings.

    Usa o padrão Singleton para garantir que apenas uma instância
    do modelo seja carregada em memória.
    """

    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
        self.model_name: str = MODEL_NAME
        self.dimensions: int = DIMENSIONS
        self.is_loaded: bool = False
        self.load_time: Optional[float] = None

    def load(self) -> None:
        """
        Carrega o modelo em memória.

        Chamado durante o startup da aplicação para garantir
        que o modelo esteja pronto antes de aceitar requisições.
        """
        if self.is_loaded:
            logger.info("Model already loaded, skipping")
            return

        logger.info(f"Loading model: {self.model_name}")
        start_time = time.time()

        try:
            self.model = SentenceTransformer(self.model_name)
            self.is_loaded = True
            self.load_time = time.time() - start_time
            logger.info(
                f"Model loaded successfully in {self.load_time:.2f}s. "
                f"Dimensions: {self.dimensions}"
            )
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Failed to load embedding model: {e}")

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Gera embeddings para uma lista de textos.

        Args:
            texts: Lista de textos para processar

        Returns:
            Lista de vetores de embedding normalizados (L2)

        Raises:
            RuntimeError: Se o modelo não estiver carregado
        """
        if not self.is_loaded or self.model is None:
            raise RuntimeError("Model not loaded")

        # Gera embeddings com normalização L2 para cosine similarity
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,  # L2 normalization
            show_progress_bar=False,
            batch_size=32  # Batch interno do modelo
        )

        # Converte numpy array para lista de listas
        return embeddings.tolist()


# Instância global do estado do modelo
model_state = ModelState()


# =============================================================================
# Lifecycle da Aplicação
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.

    - Startup: Carrega o modelo em memória
    - Shutdown: Libera recursos (se necessário)
    """
    # Startup
    logger.info("Starting Embeddings Service...")
    try:
        model_state.load()
        logger.info("Embeddings Service ready to accept requests")
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise

    yield  # Aplicação rodando

    # Shutdown
    logger.info("Shutting down Embeddings Service...")


# =============================================================================
# Aplicação FastAPI
# =============================================================================

app = FastAPI(
    title="Embeddings Service",
    description=(
        "Serviço de geração de embeddings usando sentence-transformers. "
        "Projetado como infraestrutura compartilhada para sistemas RAG."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# =============================================================================
# Endpoints
# =============================================================================

@app.post(
    "/embeddings",
    response_model=EmbeddingResponse,
    status_code=status.HTTP_200_OK,
    summary="Gerar embeddings",
    description="Gera embeddings para uma lista de textos usando all-MiniLM-L6-v2"
)
async def generate_embeddings(request: EmbeddingRequest) -> EmbeddingResponse:
    """
    Endpoint principal para geração de embeddings.

    Recebe uma lista de textos e retorna os vetores de embedding
    correspondentes. Embeddings são normalizados (L2) para uso
    com cosine similarity.

    Args:
        request: EmbeddingRequest com lista de textos

    Returns:
        EmbeddingResponse com embeddings gerados

    Raises:
        HTTPException 503: Se o modelo não estiver disponível
        HTTPException 500: Se ocorrer erro na geração
    """
    if not model_state.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded yet. Service is starting up."
        )

    try:
        logger.info(f"Generating embeddings for {len(request.texts)} texts")
        start_time = time.time()

        embeddings = model_state.generate_embeddings(request.texts)

        elapsed = time.time() - start_time
        logger.info(
            f"Generated {len(embeddings)} embeddings in {elapsed:.3f}s "
            f"({len(embeddings)/elapsed:.1f} texts/sec)"
        )

        return EmbeddingResponse(
            embeddings=embeddings,
            model=model_state.model_name,
            dimensions=model_state.dimensions
        )

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embeddings: {str(e)}"
        )


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Verifica se o serviço está saudável e pronto para receber requisições"
)
async def health_check() -> HealthResponse:
    """
    Endpoint de health check para monitoramento.

    Usado pelo Docker healthcheck e sistemas de orquestração
    para verificar se o serviço está operacional.
    """
    return HealthResponse(
        status="healthy" if model_state.is_loaded else "starting",
        model=model_state.model_name,
        dimensions=model_state.dimensions,
        model_loaded=model_state.is_loaded
    )


@app.get(
    "/info",
    response_model=ModelInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Informações do modelo",
    description="Retorna informações detalhadas sobre o modelo de embeddings"
)
async def model_info() -> ModelInfoResponse:
    """
    Retorna informações sobre o modelo e limites do serviço.

    Útil para clientes descobrirem as capacidades do serviço.
    """
    return ModelInfoResponse(
        model_name=model_state.model_name,
        dimensions=model_state.dimensions,
        max_batch_size=MAX_BATCH_SIZE,
        max_text_length=MAX_TEXT_LENGTH,
        is_local=True,
        supports_multilingual=True
    )


@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Root endpoint",
    description="Endpoint raiz com informações básicas do serviço"
)
async def root():
    """Endpoint raiz com informações básicas."""
    return {
        "service": "Embeddings Service",
        "version": "1.0.0",
        "model": MODEL_NAME,
        "dimensions": DIMENSIONS,
        "status": "ready" if model_state.is_loaded else "loading",
        "endpoints": {
            "embeddings": "POST /embeddings",
            "health": "GET /health",
            "info": "GET /info",
            "docs": "GET /docs"
        }
    }


# =============================================================================
# Tratamento de Exceções Global
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Tratamento global de exceções não capturadas."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc)}
    )
