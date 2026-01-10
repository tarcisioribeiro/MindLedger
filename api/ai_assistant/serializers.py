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
        help_text="Decisao de roteamento (local/cloud/none)"
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
