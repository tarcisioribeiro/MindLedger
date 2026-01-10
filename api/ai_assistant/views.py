"""
AI Assistant Views

API views for the AI Assistant module.
"""

import logging
import json
import time
from datetime import datetime
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse

from .serializers import QuerySerializer, QueryResponseSerializer
from security.activity_logs.models import ActivityLog
from .session_manager import get_session_manager, ConversationMessage
from .intent_classifier import get_intent_classifier
from .response_formatter import get_response_formatter

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


class AIStreamingQueryView(APIView):
    """
    AI Assistant streaming query endpoint using Server-Sent Events (SSE).

    POST /api/v1/ai/stream/

    Request body:
    {
        "question": "user question",
        "session_id": "optional-session-id",
        "top_k": 10
    }

    Response: SSE stream with events:
    - intent: Intent classification result
    - message_start: Indicates start of response
    - content_chunk: Partial answer text (streaming)
    - visualization: Visualization data (sent after text)
    - sources: Sources data
    - message_end: Indicates end of response with session_id
    - error: Error message if something fails
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Process AI Assistant streaming query."""
        serializer = QuerySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = serializer.validated_data['question']
        session_id = request.data.get('session_id')
        top_k = serializer.validated_data.get('top_k', 10)

        try:
            member = request.user.member

            # Get or create session
            session_manager = get_session_manager()
            if not session_id:
                session_id = session_manager.create_session(member.id)
                logger.info(f"Created new session: {session_id}")

            session = session_manager.get_session(session_id)
            if not session or session.user_id != member.id:
                return Response(
                    {'error': 'Invalid session'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Create streaming response
            response = StreamingHttpResponse(
                self._stream_response(question, session, member, top_k, request),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            response['Session-ID'] = session_id

            return response

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Streaming query error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _stream_response(self, question, session, member, top_k, request):
        """Generator function that yields SSE-formatted chunks."""
        try:
            # 1. Add user message to session
            session_manager = get_session_manager()
            session_manager.add_message(
                session.session_id,
                ConversationMessage(
                    role='user',
                    content=question,
                    timestamp=datetime.now()
                )
            )

            # 2. Intent classification
            intent_classifier = get_intent_classifier()
            conversation_history = [
                {'role': m.role, 'content': m.content}
                for m in session.messages[:-1]  # Exclude current user message
            ]
            intent_result = intent_classifier.classify(question, conversation_history)

            yield self._format_sse('intent', {
                'module': intent_result.module,
                'intent_type': intent_result.intent_type,
                'response_type': intent_result.response_type,
                'confidence': intent_result.confidence
            })

            # 3. RAG search and LLM generation
            from .chat.service import get_chat_service
            chat_service = get_chat_service()

            # Call existing chat service with conversation history
            response = chat_service.query(
                question=question,
                owner_id=member.id,
                top_k=top_k,
                conversation_history=conversation_history
            )

            # 4. Stream the answer (simulate streaming from complete response)
            yield self._format_sse('message_start', {})

            # Stream answer in chunks
            answer = response.answer
            chunk_size = 5  # words per chunk
            words = answer.split()

            for i in range(0, len(words), chunk_size):
                chunk = ' '.join(words[i:i + chunk_size])
                if i + chunk_size < len(words):
                    chunk += ' '
                yield self._format_sse('content_chunk', {'text': chunk})
                time.sleep(0.05)  # Small delay for smoother streaming

            # 5. Generate visualization
            response_formatter = get_response_formatter()
            # Convert response.sources to proper format for formatter
            rag_results = []
            for source in response.sources:
                class RAGResult:
                    def __init__(self, s):
                        self.module = s.get('module', 'unknown')
                        self.entity_type = s.get('type', 'unknown')
                        self.score = s.get('score', 0)
                        self.metadata = s.get('metadata', {})
                rag_results.append(RAGResult(source))

            formatted = response_formatter.format_response(
                intent_result,
                rag_results,
                answer,
                member
            )

            if formatted.visualization:
                yield self._format_sse('visualization', formatted.visualization)

            # 6. Send sources
            yield self._format_sse('sources', {'sources': formatted.sources})

            # 7. Add assistant message to session
            session_manager.add_message(
                session.session_id,
                ConversationMessage(
                    role='assistant',
                    content=answer,
                    timestamp=datetime.now(),
                    visualization=formatted.visualization,
                    sources=formatted.sources
                )
            )

            # 8. Log activity
            ActivityLog.log_action(
                user=request.user,
                action='streaming_query',
                model_name='ai_assistant',
                description=f"Streaming query: {question[:100]}...",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            # 9. End message
            yield self._format_sse('message_end', {'session_id': session.session_id})

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"Stream error: {error_detail}")

            # Log error
            ActivityLog.log_action(
                user=request.user,
                action='streaming_query_error',
                model_name='ai_assistant',
                description=f"Streaming error: {str(e)}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            yield self._format_sse('error', {'message': str(e)})

    def _format_sse(self, event_type: str, data: dict) -> str:
        """Format data as Server-Sent Event."""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


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
