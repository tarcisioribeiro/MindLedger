"""
HTTP Embedding Client
=====================
Cliente HTTP para consumir o serviço externo de embeddings.

Este cliente substitui a dependência direta de sentence-transformers,
permitindo que o modelo seja executado em um container separado.

Benefícios:
- Build rápido do container principal (sem download do modelo)
- Serviço de embeddings reutilizável por outros projetos
- Separação de responsabilidades (embeddings como infraestrutura)
- Escalabilidade independente

Uso:
    from ai_assistant.embeddings.http_client import get_http_embedding_client

    client = get_http_embedding_client()
    response = client.generate_embedding("texto para embedding")
    embeddings = response.embedding  # Lista de floats (384 dimensões)
"""

import logging
import time
from dataclasses import dataclass
from typing import List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from django.conf import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Configuração
# =============================================================================

# URL padrão do serviço de embeddings (pode ser sobrescrita via settings)
DEFAULT_EMBEDDING_SERVICE_URL = "http://embeddings:8080"

# Timeouts em segundos
DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_READ_TIMEOUT = 30.0

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 0.5
RETRY_STATUS_CODES = [500, 502, 503, 504]


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class EmbeddingResponse:
    """
    Response from embedding generation.

    Attributes:
        embedding: Vetor de embedding normalizado (L2)
        model: Nome do modelo usado
        dimensions: Número de dimensões (384 para all-MiniLM-L6-v2)
    """
    embedding: List[float]
    model: str
    dimensions: int


# =============================================================================
# Exceções
# =============================================================================

class EmbeddingServiceError(Exception):
    """Erro base para o serviço de embeddings."""
    pass


class EmbeddingServiceUnavailable(EmbeddingServiceError):
    """Serviço de embeddings não está disponível."""
    pass


class EmbeddingGenerationFailed(EmbeddingServiceError):
    """Falha na geração de embeddings."""
    pass


# =============================================================================
# HTTP Embedding Client
# =============================================================================

class HTTPEmbeddingClient:
    """
    Cliente HTTP para o serviço de embeddings.

    Características:
    - Retry automático com backoff exponencial
    - Timeouts configuráveis
    - Connection pooling via requests Session
    - Logging detalhado para debugging

    Attributes:
        base_url: URL base do serviço de embeddings
        model_name: Nome do modelo (informativo, definido pelo serviço)
        dimensions: Dimensões do embedding (384)
    """

    DEFAULT_MODEL = 'all-MiniLM-L6-v2'
    DEFAULT_DIMENSIONS = 384

    def __init__(
        self,
        base_url: Optional[str] = None,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
        read_timeout: float = DEFAULT_READ_TIMEOUT
    ):
        """
        Inicializa o cliente HTTP.

        Args:
            base_url: URL do serviço de embeddings (default: http://embeddings:8080)
            connect_timeout: Timeout de conexão em segundos
            read_timeout: Timeout de leitura em segundos
        """
        # Obtém URL das configurações ou usa default
        self.base_url = (
            base_url or
            getattr(settings, 'EMBEDDING_SERVICE_URL', None) or
            DEFAULT_EMBEDDING_SERVICE_URL
        )
        self.base_url = self.base_url.rstrip('/')

        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.model_name = self.DEFAULT_MODEL
        self.dimensions = self.DEFAULT_DIMENSIONS

        # Configura session com retry
        self._session = self._create_session()

        logger.info(f"HTTPEmbeddingClient initialized with base_url: {self.base_url}")

    def _create_session(self) -> requests.Session:
        """
        Cria uma session HTTP com retry configurado.

        Returns:
            Session configurada com retry e connection pooling
        """
        session = requests.Session()

        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_BACKOFF_FACTOR,
            status_forcelist=RETRY_STATUS_CODES,
            allowed_methods=["GET", "POST"]
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def is_available(self) -> bool:
        """
        Verifica se o serviço de embeddings está disponível.

        Returns:
            True se o serviço está respondendo ao health check
        """
        try:
            response = self._session.get(
                f"{self.base_url}/health",
                timeout=(self.connect_timeout, self.read_timeout)
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('model_loaded', False)
            return False
        except Exception as e:
            logger.warning(f"Embedding service health check failed: {e}")
            return False

    def health_check(self) -> bool:
        """
        Alias para is_available() para compatibilidade com interface existente.
        """
        return self.is_available()

    def generate_embedding(self, text: str) -> EmbeddingResponse:
        """
        Gera embedding para um único texto.

        Args:
            text: Texto para gerar embedding

        Returns:
            EmbeddingResponse com o vetor de embedding

        Raises:
            ValueError: Se o texto for vazio
            EmbeddingServiceUnavailable: Se o serviço não estiver disponível
            EmbeddingGenerationFailed: Se a geração falhar
        """
        if not text or not text.strip():
            raise ValueError("Empty text provided")

        # Usa o endpoint batch com um único texto
        responses = self.generate_embeddings_batch([text])
        return responses[0]

    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[EmbeddingResponse]:
        """
        Gera embeddings para múltiplos textos em batch.

        O parâmetro batch_size é mantido para compatibilidade com a interface
        existente, mas o batching real é feito pelo serviço de embeddings.

        Args:
            texts: Lista de textos para gerar embeddings
            batch_size: Ignorado (mantido para compatibilidade)

        Returns:
            Lista de EmbeddingResponse, um para cada texto

        Raises:
            ValueError: Se a lista de textos for vazia ou todos os textos forem vazios
            EmbeddingServiceUnavailable: Se o serviço não estiver disponível
            EmbeddingGenerationFailed: Se a geração falhar
        """
        if not texts:
            raise ValueError("Empty texts list provided")

        # Filtra textos vazios
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("All texts are empty")

        try:
            start_time = time.time()

            response = self._session.post(
                f"{self.base_url}/embeddings",
                json={"texts": valid_texts},
                timeout=(self.connect_timeout, self.read_timeout),
                headers={"Content-Type": "application/json"}
            )

            elapsed = time.time() - start_time

            if response.status_code == 503:
                raise EmbeddingServiceUnavailable(
                    "Embedding service is starting up. Please try again."
                )

            if response.status_code != 200:
                error_detail = response.json().get('detail', 'Unknown error')
                raise EmbeddingGenerationFailed(
                    f"Embedding generation failed: {error_detail}"
                )

            data = response.json()
            embeddings = data.get('embeddings', [])
            model = data.get('model', self.DEFAULT_MODEL)
            dimensions = data.get('dimensions', self.DEFAULT_DIMENSIONS)

            logger.debug(
                f"Generated {len(embeddings)} embeddings in {elapsed:.3f}s "
                f"via HTTP ({len(embeddings)/elapsed:.1f} texts/sec)"
            )

            # Converte para lista de EmbeddingResponse
            return [
                EmbeddingResponse(
                    embedding=emb,
                    model=model,
                    dimensions=dimensions
                )
                for emb in embeddings
            ]

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection to embedding service failed: {e}")
            raise EmbeddingServiceUnavailable(
                f"Cannot connect to embedding service at {self.base_url}: {e}"
            )

        except requests.exceptions.Timeout as e:
            logger.error(f"Embedding service request timed out: {e}")
            raise EmbeddingServiceUnavailable(
                f"Embedding service request timed out: {e}"
            )

        except (EmbeddingServiceUnavailable, EmbeddingGenerationFailed):
            raise

        except Exception as e:
            logger.error(f"Unexpected error in embedding generation: {e}")
            raise EmbeddingGenerationFailed(f"Failed to generate embeddings: {e}")

    def get_model_info(self) -> dict:
        """
        Obtém informações sobre o modelo do serviço de embeddings.

        Returns:
            Dict com informações do modelo
        """
        try:
            response = self._session.get(
                f"{self.base_url}/info",
                timeout=(self.connect_timeout, self.read_timeout)
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get model info: {e}")

        # Retorna informações padrão se não conseguir conectar
        return {
            'model_name': self.model_name,
            'dimensions': self.dimensions,
            'is_local': False,  # False porque roda em outro container
            'is_loaded': self.is_available(),
            'supports_multilingual': True,
            'service_url': self.base_url
        }

    def close(self):
        """Fecha a session HTTP."""
        if self._session:
            self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# =============================================================================
# Singleton Instance
# =============================================================================

_http_embedding_client: Optional[HTTPEmbeddingClient] = None


def get_http_embedding_client(
    base_url: Optional[str] = None
) -> HTTPEmbeddingClient:
    """
    Obtém a instância singleton do HTTPEmbeddingClient.

    Args:
        base_url: URL do serviço (apenas usado na primeira chamada)

    Returns:
        Instância configurada do HTTPEmbeddingClient
    """
    global _http_embedding_client
    if _http_embedding_client is None:
        _http_embedding_client = HTTPEmbeddingClient(base_url)
    return _http_embedding_client


def reset_http_embedding_client():
    """
    Reseta o cliente singleton.

    Útil para testes ou quando a URL do serviço precisa mudar.
    """
    global _http_embedding_client
    if _http_embedding_client is not None:
        _http_embedding_client.close()
    _http_embedding_client = None
