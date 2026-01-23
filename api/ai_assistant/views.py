"""
Views para o módulo AI Assistant.

Expõe endpoints para interação com o assistente de IA.
"""
import time
import logging
from typing import Optional

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from members.models import Member
from .models import ConversationHistory
from .services import QueryInterpreter, DatabaseExecutor, OllamaClient
from .services.database_executor import DatabaseError


logger = logging.getLogger(__name__)


def get_member_for_user(user) -> Optional[Member]:
    """
    Obtém o Member associado ao usuário.

    Args:
        user: Usuário autenticado

    Returns:
        Member ou None se não encontrado
    """
    try:
        return Member.objects.filter(user=user, deleted_at__isnull=True).first()
    except Exception:
        return None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pergunta(request: Request) -> Response:
    """
    Processa uma pergunta em linguagem natural.

    Endpoint: POST /api/v1/ai/pergunta/

    Body:
        {
            "pergunta": "Qual foi meu faturamento do último mês?"
        }

    Returns:
        {
            "resposta": "O faturamento do último mês foi R$ 12.345,00.",
            "display_type": "currency",
            "data": [...],
            "module": "revenues",
            "success": true
        }
    """
    start_time = time.time()

    # Validação do body
    pergunta_texto = request.data.get('pergunta', '').strip()
    if not pergunta_texto:
        return Response(
            {'error': 'O campo "pergunta" é obrigatório.'},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    if len(pergunta_texto) > 500:
        return Response(
            {'error': 'A pergunta deve ter no máximo 500 caracteres.'},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    # Obtém o member do usuário
    member = get_member_for_user(request.user)
    if not member:
        return Response(
            {'error': 'Usuário não possui perfil de membro configurado.'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        # 1. Interpreta a pergunta e gera SQL
        query_result = QueryInterpreter.interpret(pergunta_texto, member.id)

        # 2. Se não identificou o módulo, retorna mensagem amigável
        if query_result.module == 'unknown':
            response_data = {
                'resposta': (
                    'Desculpe, não consegui entender sua pergunta. '
                    'Tente perguntar sobre:\n'
                    '- Receitas e faturamento\n'
                    '- Despesas e gastos\n'
                    '- Saldo das contas\n'
                    '- Cartões de crédito\n'
                    '- Empréstimos\n'
                    '- Livros e leituras\n'
                    '- Tarefas e objetivos\n'
                    '- Senhas armazenadas\n'
                    '- Cofres e reservas'
                ),
                'display_type': 'text',
                'data': [],
                'module': 'unknown',
                'success': True
            }
            _save_history(
                member, pergunta_texto, query_result,
                [], response_data['resposta'], 'text',
                int((time.time() - start_time) * 1000), True
            )
            return Response(response_data)

        # 3. Executa a query no banco
        db_result = DatabaseExecutor.execute(query_result)

        # 4. Gera resposta com Ollama
        ollama = OllamaClient()
        resposta = ollama.generate_response(
            query_description=db_result['description'],
            data=db_result['data'],
            display_type=db_result['display_type'],
            module=db_result['module']
        )

        # 5. Calcula tempo de resposta
        response_time_ms = int((time.time() - start_time) * 1000)

        # 6. Salva histórico
        _save_history(
            member, pergunta_texto, query_result,
            db_result['data'], resposta, db_result['display_type'],
            response_time_ms, True
        )

        # 7. Retorna resposta
        return Response({
            'resposta': resposta,
            'display_type': db_result['display_type'],
            'data': db_result['data'],
            'module': db_result['module'],
            'count': db_result['count'],
            'description': db_result['description'],
            'success': True
        })

    except DatabaseError as e:
        logger.error(f"Database error processing question: {e}")
        response_time_ms = int((time.time() - start_time) * 1000)
        _save_history(
            member, pergunta_texto, None, [],
            str(e), 'text', response_time_ms, False, str(e)
        )
        return Response(
            {'error': 'Erro ao consultar dados. Tente novamente.', 'success': False},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.exception(f"Unexpected error processing question: {e}")
        response_time_ms = int((time.time() - start_time) * 1000)
        _save_history(
            member, pergunta_texto, None, [],
            str(e), 'text', response_time_ms, False, str(e)
        )
        return Response(
            {'error': 'Erro inesperado. Tente novamente.', 'success': False},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historico(request: Request) -> Response:
    """
    Retorna o histórico de conversas do usuário.

    Endpoint: GET /api/v1/ai/historico/

    Query params:
        limit: Número máximo de registros (default: 20, max: 100)

    Returns:
        Lista de conversas anteriores
    """
    member = get_member_for_user(request.user)
    if not member:
        return Response(
            {'error': 'Usuário não possui perfil de membro.'},
            status=status.HTTP_403_FORBIDDEN
        )

    limit = min(int(request.query_params.get('limit', 20)), 100)

    conversations = ConversationHistory.objects.filter(
        owner=member,
        deleted_at__isnull=True
    ).order_by('-created_at')[:limit]

    data = [
        {
            'id': c.id,
            'question': c.question,
            'response': c.ai_response,
            'module': c.detected_module,
            'display_type': c.display_type,
            'success': c.success,
            'created_at': c.created_at.isoformat(),
        }
        for c in conversations
    ]

    return Response({'conversations': data, 'count': len(data)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health(request: Request) -> Response:
    """
    Verifica saúde do serviço de IA.

    Endpoint: GET /api/v1/ai/health/

    Returns:
        Status do Ollama e do banco de dados
    """
    ollama = OllamaClient()
    ollama_ok = ollama.check_health()

    # Verifica conexão com banco
    db_ok = False
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        db_ok = True
    except Exception:
        pass

    status_code = status.HTTP_200_OK if (ollama_ok and db_ok) else status.HTTP_503_SERVICE_UNAVAILABLE

    return Response({
        'ollama': 'healthy' if ollama_ok else 'unavailable',
        'database': 'healthy' if db_ok else 'unavailable',
        'model': ollama.model,
    }, status=status_code)


def _save_history(
    member: Member,
    question: str,
    query_result: Optional[object],
    data: list,
    response: str,
    display_type: str,
    response_time_ms: int,
    success: bool,
    error_message: Optional[str] = None
):
    """
    Salva histórico de conversa no banco.

    Não lança exceção para não afetar a resposta ao usuário.
    """
    try:
        ConversationHistory.objects.create(
            question=question,
            detected_module=query_result.module if query_result else None,
            generated_sql=query_result.sql[:500] if query_result and query_result.sql else None,
            query_result_count=len(data),
            ai_response=response[:2000],  # Limita tamanho
            display_type=display_type,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message[:500] if error_message else None,
            owner=member
        )
    except Exception as e:
        logger.warning(f"Failed to save conversation history: {e}")
