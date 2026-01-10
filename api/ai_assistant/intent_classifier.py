"""
Intent Classifier for AI Assistant

Analyzes user questions to determine:
- Module (finance, security, library, planning)
- Intent type (aggregation, trend, comparison, lookup, list)
- Response type (chart, cards, table, text)
- Extracted entities (dates, categories, amounts)

Uses rule-based keyword matching for fast, predictable classification.
Can be enhanced with LLM-based classification in the future.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta


@dataclass
class IntentResult:
    """Result of intent classification."""
    module: str  # finance, security, library, planning
    intent_type: str  # aggregation, trend, comparison, lookup, list
    response_type: str  # chart, cards, table, text
    entities: Dict[str, Any]  # extracted entities
    confidence: float  # 0.0 to 1.0


class IntentClassifier:
    """
    Rule-based intent classifier using keyword matching.

    Future enhancement: Could use LLM-based classification for better accuracy.
    """

    # Keywords for module detection
    MODULE_KEYWORDS = {
        'finance': [
            'despesa', 'gasto', 'receita', 'conta', 'saldo', 'cartão', 'cartao',
            'empréstimo', 'emprestimo', 'transferência', 'transferencia',
            'dinheiro', 'pago', 'valor', 'gastei', 'paguei', 'recebi',
            'compra', 'venda', 'débito', 'debito', 'crédito', 'credito',
            'fatura', 'parcela', 'juros', 'taxa', 'rendimento', 'investimento'
        ],
        'security': [
            'senha', 'password', 'arquivo', 'seguro', 'segurança', 'seguranca',
            'credencial', 'login', 'acesso', 'documento', 'certificado'
        ],
        'library': [
            'livro', 'autor', 'leitura', 'ler', 'lendo', 'resumo', 'página', 'pagina',
            'capítulo', 'capitulo', 'bibliografia', 'obra', 'texto', 'literário', 'literario'
        ],
        'planning': [
            'tarefa', 'objetivo', 'meta', 'rotina', 'hábito', 'habito',
            'planejamento', 'diário', 'diario', 'reflexão', 'reflexao',
            'progresso', 'completar', 'realizar', 'alcançar', 'alcancar'
        ]
    }

    # Keywords for intent type detection
    INTENT_KEYWORDS = {
        'aggregation': [
            'total', 'quanto', 'quantos', 'quantas', 'soma', 'somatório', 'somatorio',
            'maior', 'menor', 'média', 'media', 'máximo', 'maximo', 'mínimo', 'minimo',
            'tudo', 'todos', 'todas'
        ],
        'trend': [
            'tendência', 'tendencia', 'evolução', 'evolucao', 'crescimento',
            'histórico', 'historico', 'ao longo', 'período', 'periodo',
            'meses', 'semanas', 'dias', 'anos'
        ],
        'comparison': [
            'comparar', 'comparação', 'comparacao', 'diferença', 'diferenca',
            'versus', 'vs', 'melhor', 'pior', 'entre'
        ],
        'lookup': [
            'qual', 'quais', 'onde', 'quando', 'como',
            'encontre', 'encontrar', 'busque', 'buscar', 'procure', 'procurar'
        ],
        'list': [
            'liste', 'listar', 'mostre', 'mostrar', 'exiba', 'exibir',
            'últimos', 'ultimos', 'recentes', 'primeiros'
        ]
    }

    # Response type mapping rules
    RESPONSE_TYPE_RULES = {
        # (intent_type, module): response_type
        ('aggregation', 'finance'): 'cards',
        ('aggregation', 'security'): 'cards',
        ('aggregation', 'library'): 'cards',
        ('aggregation', 'planning'): 'cards',
        ('trend', 'finance'): 'chart',
        ('trend', 'library'): 'chart',
        ('trend', 'planning'): 'chart',
        ('comparison', 'finance'): 'chart',
        ('comparison', 'library'): 'chart',
        ('list', 'any'): 'table',
        ('lookup', 'any'): 'text',
    }

    # Category keywords for finance module
    FINANCE_CATEGORIES = [
        'alimentação', 'alimentacao', 'comida', 'restaurante', 'supermercado',
        'transporte', 'combustível', 'combustivel', 'uber', 'taxi', 'ônibus', 'onibus',
        'saúde', 'saude', 'médico', 'medico', 'farmácia', 'farmacia', 'hospital',
        'educação', 'educacao', 'curso', 'faculdade', 'escola',
        'lazer', 'entretenimento', 'cinema', 'show', 'viagem',
        'moradia', 'aluguel', 'condomínio', 'condominio', 'água', 'agua', 'luz', 'internet',
        'vestuário', 'vestuario', 'roupa', 'calçado', 'calcado'
    ]

    def classify(
        self,
        question: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> IntentResult:
        """
        Classify user question into intent and determine response type.

        Args:
            question: User's question
            conversation_history: Previous messages (for context)

        Returns:
            IntentResult with classification details
        """
        question_lower = question.lower()

        # 1. Detect module
        module = self._detect_module(question_lower, conversation_history)

        # 2. Detect intent type
        intent_type = self._detect_intent_type(question_lower)

        # 3. Extract entities (dates, categories, amounts)
        entities = self._extract_entities(question_lower, module)

        # 4. Determine response type
        response_type = self._determine_response_type(
            intent_type, module, question_lower
        )

        # 5. Calculate confidence
        confidence = self._calculate_confidence(question_lower, module, intent_type)

        return IntentResult(
            module=module,
            intent_type=intent_type,
            response_type=response_type,
            entities=entities,
            confidence=confidence
        )

    def _detect_module(
        self,
        question: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """Detect which module the question is about."""
        scores = {}
        for module, keywords in self.MODULE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in question)
            scores[module] = score

        # Check conversation history for context
        if conversation_history and max(scores.values()) == 0:
            # Look at last user message for context
            for msg in reversed(conversation_history):
                if msg['role'] == 'user':
                    msg_lower = msg['content'].lower()
                    for module, keywords in self.MODULE_KEYWORDS.items():
                        if any(kw in msg_lower for kw in keywords):
                            return module
                    break

        # Return module with highest score, default to finance
        if max(scores.values()) > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        return 'finance'

    def _detect_intent_type(self, question: str) -> str:
        """Detect the type of intent (aggregation, trend, etc.)."""
        scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in question)
            scores[intent] = score

        # Return intent with highest score, default to lookup
        if max(scores.values()) > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        return 'lookup'

    def _extract_entities(self, question: str, module: str) -> Dict[str, Any]:
        """
        Extract entities from the question.

        Entities include:
        - date_range: start and end dates
        - categories: list of categories (for finance)
        - amount: numeric value
        - limit: number of results (e.g., "top 5", "últimos 10")
        """
        entities = {}

        # Date extraction
        now = datetime.now()

        if any(phrase in question for phrase in ['este mês', 'mês atual', 'esse mês']):
            entities['date_range'] = {
                'start': now.replace(day=1).strftime('%Y-%m-%d'),
                'end': now.strftime('%Y-%m-%d'),
                'label': 'este mês'
            }
        elif any(phrase in question for phrase in ['último mês', 'ultimo mês', 'mês passado', 'mes passado']):
            last_month = now.replace(day=1) - timedelta(days=1)
            entities['date_range'] = {
                'start': last_month.replace(day=1).strftime('%Y-%m-%d'),
                'end': last_month.strftime('%Y-%m-%d'),
                'label': 'último mês'
            }
        elif any(phrase in question for phrase in ['este ano', 'ano atual', 'esse ano']):
            entities['date_range'] = {
                'start': now.replace(month=1, day=1).strftime('%Y-%m-%d'),
                'end': now.strftime('%Y-%m-%d'),
                'label': 'este ano'
            }
        elif any(phrase in question for phrase in ['última semana', 'ultima semana', 'semana passada']):
            week_ago = now - timedelta(days=7)
            entities['date_range'] = {
                'start': week_ago.strftime('%Y-%m-%d'),
                'end': now.strftime('%Y-%m-%d'),
                'label': 'última semana'
            }

        # Amount extraction (R$ 1000, 1000 reais)
        amount_match = re.search(r'R?\$?\s*(\d+(?:[.,]\d+)?)', question)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '.')
            try:
                entities['amount'] = float(amount_str)
            except ValueError:
                pass

        # Limit extraction ("top 5", "últimos 10", "5 maiores")
        limit_match = re.search(r'(?:top|últimos?|ultimos?|primeiros?|maiores?|menores?)\s+(\d+)', question)
        if limit_match:
            entities['limit'] = int(limit_match.group(1))
        elif any(phrase in question for phrase in ['top 5', '5 maiores', '5 menores']):
            entities['limit'] = 5

        # Category detection (for finance module)
        if module == 'finance':
            found_categories = [cat for cat in self.FINANCE_CATEGORIES if cat in question]
            if found_categories:
                entities['categories'] = found_categories

        return entities

    def _determine_response_type(
        self,
        intent: str,
        module: str,
        question: str
    ) -> str:
        """Determine the appropriate response visualization type."""
        # Check specific rules
        key = (intent, module)
        if key in self.RESPONSE_TYPE_RULES:
            return self.RESPONSE_TYPE_RULES[key]

        # Check generic rules
        key = (intent, 'any')
        if key in self.RESPONSE_TYPE_RULES:
            return self.RESPONSE_TYPE_RULES[key]

        # Keyword overrides for explicit visualization requests
        if any(kw in question for kw in ['gráfico', 'grafico', 'chart', 'visualizar']):
            return 'chart'

        if any(kw in question for kw in ['lista', 'tabela', 'todos', 'todas']):
            return 'table'

        if any(kw in question for kw in ['total', 'soma', 'quanto']):
            return 'cards'

        # Default to text for conversational queries
        return 'text'

    def _calculate_confidence(
        self,
        question: str,
        module: str,
        intent: str
    ) -> float:
        """
        Calculate confidence score based on keyword matches.

        Returns a value between 0.0 and 1.0.
        """
        module_keywords = self.MODULE_KEYWORDS.get(module, [])
        intent_keywords = self.INTENT_KEYWORDS.get(intent, [])

        module_matches = sum(1 for kw in module_keywords if kw in question)
        intent_matches = sum(1 for kw in intent_keywords if kw in question)

        total_matches = module_matches + intent_matches
        total_possible = max(len(module_keywords) + len(intent_keywords), 1)

        # Normalize to 0-1 range with a minimum threshold
        confidence = min(total_matches / (total_possible * 0.1), 1.0)

        # Boost confidence if question length is appropriate (not too short)
        words = question.split()
        if len(words) >= 3:
            confidence = min(confidence * 1.2, 1.0)

        return round(confidence, 3)


# Singleton instance
_intent_classifier: Optional[IntentClassifier] = None


def get_intent_classifier() -> IntentClassifier:
    """
    Get the singleton IntentClassifier instance.

    Returns:
        The global IntentClassifier instance
    """
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
