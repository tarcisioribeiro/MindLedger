"""
AI Assistant Views

API views for the AI Assistant module.
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .serializers import QuerySerializer, QueryResponseSerializer
from security.activity_logs.models import ActivityLog

logger = logging.getLogger(__name__)


class AIQueryView(APIView):
    """
    AI Assistant query endpoint.

    POST /api/v1/ai/query/

    Accepts natural language questions and returns AI-generated answers
    based on the user's personal data across all modules.

    The assistant semantically searches across:
    - Finance: Expenses, revenues, accounts, credit cards, loans
    - Security: Passwords, stored credentials
    - Library: Books, summaries, readings
    - Planning: Goals, routine tasks, reflections

    And returns a contextualized AI-generated response using
    intelligent LLM routing based on data sensitivity.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Process AI Assistant query."""
        serializer = QuerySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = serializer.validated_data['question']
        top_k = serializer.validated_data.get('top_k', 10)

        try:
            # Get user's member
            member = request.user.member
            result = self._process_query(question, member, top_k)

            # Log activity
            ActivityLog.log_action(
                user=request.user,
                action='query',
                model_name='ai_assistant',
                description=f"Consulta AI: {question[:100]}...",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            response_serializer = QueryResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            # Configuration errors (API keys not set, services unavailable)
            error_msg = str(e)
            logger.error(f"AI configuration error: {error_msg}")

            ActivityLog.log_action(
                user=request.user,
                action='query_error',
                model_name='ai_assistant',
                description=f"Erro de configuracao AI: {error_msg}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            return Response(
                {
                    'error': 'Configuracao necessaria',
                    'message': error_msg,
                    'detail': 'Verifique se Ollama esta rodando e os modelos estao instalados.'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except RuntimeError as e:
            # Runtime errors (service unavailable, etc.)
            error_msg = str(e)
            logger.error(f"AI runtime error: {error_msg}")

            ActivityLog.log_action(
                user=request.user,
                action='query_error',
                model_name='ai_assistant',
                description=f"Erro de runtime AI: {error_msg}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            return Response(
                {
                    'error': 'Servico indisponivel',
                    'message': error_msg,
                    'detail': 'O servico de IA esta temporariamente indisponivel.'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except Exception as e:
            # Unexpected errors
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"AI unexpected error: {error_detail}")

            ActivityLog.log_action(
                user=request.user,
                action='query_error',
                model_name='ai_assistant',
                description=f"Erro na consulta AI: {str(e)}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            return Response(
                {
                    'error': 'Erro ao processar consulta',
                    'message': str(e),
                    'detail': 'Ocorreu um erro inesperado. Verifique os logs do servidor.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _process_query(self, question: str, member, top_k: int) -> dict:
        """
        Process query using the RAG architecture.

        Uses:
        - Local Ollama for embeddings (nomic-embed-text)
        - pgvector for semantic search
        - Intelligent routing: Ollama for sensitive, Groq for complex
        - Redis cache for performance
        """
        from .chat.service import get_chat_service

        chat_service = get_chat_service()
        response = chat_service.query(
            question=question,
            owner_id=member.id,
            top_k=top_k
        )

        # Format response for serializer compatibility
        return {
            'answer': response.answer,
            'sources': [
                {
                    'module': source.get('tipo', 'unknown'),
                    'type': source.get('content_type', 'unknown'),
                    'score': source.get('score', 0),
                    'metadata': source.get('metadata', {})
                }
                for source in response.sources
            ],
            'routing_decision': response.routing_decision,
            'provider': response.provider,
            'cached': response.cached
        }


class AIStatusView(APIView):
    """
    AI Assistant status endpoint.

    GET /api/v1/ai/status/

    Returns the status of all AI services.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get AI services status."""
        try:
            from .chat.service import get_chat_service

            chat_service = get_chat_service()
            status_info = chat_service.get_status()

            return Response({
                'status': 'ok',
                'services': status_info
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
