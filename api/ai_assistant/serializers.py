from rest_framework import serializers


class QuerySerializer(serializers.Serializer):
    """Serializer for AI Assistant query requests."""
    question = serializers.CharField(
        required=True,
        help_text="Pergunta ou consulta do usuario",
        max_length=1000
    )
    top_k = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=50,
        help_text="Numero de resultados relevantes a considerar"
    )


class QueryResponseSerializer(serializers.Serializer):
    """Serializer for AI Assistant query responses."""
    answer = serializers.CharField(help_text="Resposta gerada pelo AI Assistant")
    routing_decision = serializers.CharField(
        required=False,
        help_text="Decisao de roteamento (local/cloud/sql/none)"
    )
    provider = serializers.CharField(
        required=False,
        help_text="Provedor LLM utilizado (ollama/groq)"
    )
    cached = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Se a resposta veio do cache"
    )
    # SQL-specific fields
    sql_query = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Query SQL executada (quando execution_mode=sql)"
    )
    sql_explanation = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Explicacao da query SQL gerada"
    )
    data_rows = serializers.ListField(
        required=False,
        allow_null=True,
        child=serializers.DictField(),
        help_text="Dados retornados pela query SQL"
    )
    execution_mode = serializers.CharField(
        required=False,
        default='rag',
        help_text="Modo de execucao utilizado (sql/rag/hybrid)"
    )
    visualization = serializers.DictField(
        required=False,
        allow_null=True,
        help_text="Configuracao de visualizacao (chart/cards/table)"
    )


class IntentResultSerializer(serializers.Serializer):
    """Serializer for intent classification results."""
    module = serializers.CharField(help_text="Modulo detectado (finance/library/security/planning)")
    intent_type = serializers.CharField(help_text="Tipo de intencao (aggregation/list/trend/lookup)")
    response_type = serializers.CharField(help_text="Tipo de resposta sugerido (chart/cards/table/text)")
    execution_mode = serializers.CharField(help_text="Modo de execucao (sql/rag/hybrid)")
    confidence = serializers.FloatField(help_text="Confianca da classificacao (0-1)")
