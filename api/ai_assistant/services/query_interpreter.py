"""
Interpretador de perguntas em linguagem natural para SQL.

Usa regras baseadas em palavras-chave para identificar módulos e gerar queries.
Expansível: adicione novas regras conforme necessário.
"""
import re
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
from datetime import date, timedelta
from django.utils import timezone


@dataclass
class QueryResult:
    """Resultado da interpretação de uma pergunta."""
    module: str
    sql: str
    params: Tuple
    display_type: str  # 'text', 'table', 'list', 'currency', 'password'
    description: str
    requires_decryption: bool = False
    decryption_fields: List[str] = None

    def __post_init__(self):
        if self.decryption_fields is None:
            self.decryption_fields = []


class QueryInterpreter:
    """
    Interpreta perguntas em português e gera SQL correspondente.

    Usa mapeamento de palavras-chave para identificar intenção e módulo.
    """

    # Mapeamento de palavras-chave para módulos
    MODULE_KEYWORDS: Dict[str, List[str]] = {
        'revenues': [
            'faturamento', 'receita', 'receitas', 'ganho', 'ganhos',
            'entrada', 'entradas', 'salário', 'salario', 'rendimento',
            'rendimentos', 'recebido', 'recebidos', 'quanto ganhei',
            'quanto recebi', 'renda', 'reembolso', 'cashback'
        ],
        'expenses': [
            'despesa', 'despesas', 'gasto', 'gastos', 'conta', 'contas a pagar',
            'quanto gastei', 'pagamento', 'pagamentos', 'compra', 'compras',
            'débito', 'debito', 'saída', 'saida', 'custo', 'custos'
        ],
        'accounts': [
            'saldo', 'saldos', 'conta bancária', 'conta bancaria', 'banco',
            'nubank', 'sicoob', 'mercado pago', 'caixa', 'bradesco', 'itaú',
            'itau', 'santander', 'inter', 'c6', 'picpay', 'dinheiro disponível',
            'quanto tenho', 'minha conta', 'minhas contas'
        ],
        'credit_cards': [
            'cartão', 'cartao', 'cartões', 'cartoes', 'fatura', 'faturas',
            'limite', 'crédito disponível', 'credito disponivel',
            'cartão de crédito', 'cartao de credito', 'visa', 'mastercard',
            'elo', 'american express', 'hipercard'
        ],
        'loans': [
            'empréstimo', 'emprestimo', 'empréstimos', 'emprestimos',
            'dívida', 'divida', 'dívidas', 'dividas', 'devo', 'devendo',
            'me devem', 'emprestei', 'peguei emprestado'
        ],
        'library': [
            'livro', 'livros', 'leitura', 'leituras', 'lendo', 'li',
            'autor', 'autores', 'editora', 'editoras', 'resumo', 'resumos',
            'biblioteca', 'páginas', 'paginas', 'obra', 'obras', 'título'
        ],
        'personal_planning': [
            'tarefa', 'tarefas', 'rotina', 'hábito', 'habito', 'hábitos',
            'habitos', 'objetivo', 'objetivos', 'meta', 'metas', 'hoje',
            'agenda', 'checklist', 'planejamento', 'afazer', 'afazeres',
            'pendente', 'pendentes', 'concluído', 'concluido'
        ],
        'security': [
            'senha', 'senhas', 'password', 'credencial', 'credenciais',
            'login', 'acesso', 'site', 'sites', 'netflix', 'spotify',
            'amazon', 'google', 'facebook', 'instagram', 'twitter',
            'linkedin', 'github', 'email'
        ],
        'vaults': [
            'cofre', 'cofres', 'reserva', 'reservas', 'poupança', 'poupanca',
            'guardado', 'guardei', 'investimento', 'investimentos', 'rendimento',
            'aplicação', 'aplicacao', 'aplicações', 'aplicacoes'
        ],
        'transfers': [
            'transferência', 'transferencia', 'transferências', 'transferencias',
            'pix', 'ted', 'doc', 'transferi', 'enviei', 'mandei dinheiro'
        ],
    }

    # Mapeamento de períodos temporais
    TIME_KEYWORDS: Dict[str, Tuple[Optional[date], Optional[date]]] = {}

    @classmethod
    def _get_time_range(cls, question: str) -> Tuple[Optional[date], Optional[date], str]:
        """
        Extrai o período temporal da pergunta.

        Returns:
            Tupla com (data_inicio, data_fim, descrição_período)
        """
        today = timezone.now().date()
        question_lower = question.lower()

        # Hoje
        if any(w in question_lower for w in ['hoje', 'dia de hoje', 'neste dia']):
            return today, today, 'hoje'

        # Ontem
        if 'ontem' in question_lower:
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday, 'ontem'

        # Esta semana
        if any(w in question_lower for w in ['esta semana', 'essa semana', 'semana atual']):
            start = today - timedelta(days=today.weekday())
            return start, today, 'esta semana'

        # Semana passada
        if any(w in question_lower for w in ['semana passada', 'última semana', 'ultima semana']):
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
            return start, end, 'semana passada'

        # Este mês
        if any(w in question_lower for w in ['este mês', 'este mes', 'mês atual', 'mes atual', 'neste mês', 'neste mes']):
            start = today.replace(day=1)
            return start, today, 'este mês'

        # Mês passado / último mês
        if any(w in question_lower for w in ['mês passado', 'mes passado', 'último mês', 'ultimo mes']):
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            return first_day_last_month, last_day_last_month, 'mês passado'

        # Últimos X dias
        match = re.search(r'últimos?\s+(\d+)\s+dias?', question_lower)
        if not match:
            match = re.search(r'ultimos?\s+(\d+)\s+dias?', question_lower)
        if match:
            days = int(match.group(1))
            start = today - timedelta(days=days)
            return start, today, f'últimos {days} dias'

        # Este ano
        if any(w in question_lower for w in ['este ano', 'ano atual', 'neste ano']):
            start = today.replace(month=1, day=1)
            return start, today, 'este ano'

        # Ano passado
        if any(w in question_lower for w in ['ano passado', 'último ano', 'ultimo ano']):
            start = today.replace(year=today.year - 1, month=1, day=1)
            end = today.replace(year=today.year - 1, month=12, day=31)
            return start, end, 'ano passado'

        # Mês específico (janeiro, fevereiro, etc.)
        months = {
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
            'abril': 4, 'maio': 5, 'junho': 6, 'julho': 7,
            'agosto': 8, 'setembro': 9, 'outubro': 10,
            'novembro': 11, 'dezembro': 12
        }
        for month_name, month_num in months.items():
            if month_name in question_lower:
                year = today.year
                # Se o mês mencionado é posterior ao atual, assume ano anterior
                if month_num > today.month:
                    year -= 1
                start = date(year, month_num, 1)
                if month_num == 12:
                    end = date(year, 12, 31)
                else:
                    end = date(year, month_num + 1, 1) - timedelta(days=1)
                return start, end, month_name.capitalize()

        # Sem período específico - retorna None para usar todos os dados
        return None, None, 'todo o período'

    @classmethod
    def _detect_module(cls, question: str) -> str:
        """Detecta o módulo baseado em palavras-chave."""
        question_lower = question.lower()

        # Conta ocorrências de palavras-chave por módulo
        scores: Dict[str, int] = {}
        for module, keywords in cls.MODULE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in question_lower)
            if score > 0:
                scores[module] = score

        if not scores:
            return 'unknown'

        # Retorna o módulo com maior score
        return max(scores, key=scores.get)

    @classmethod
    def _detect_aggregation(cls, question: str) -> str:
        """Detecta tipo de agregação desejada."""
        question_lower = question.lower()

        if any(w in question_lower for w in ['total', 'soma', 'somado', 'somar']):
            return 'sum'
        if any(w in question_lower for w in ['média', 'media', 'médio', 'medio']):
            return 'avg'
        if any(w in question_lower for w in ['máximo', 'maximo', 'maior', 'mais alto']):
            return 'max'
        if any(w in question_lower for w in ['mínimo', 'minimo', 'menor', 'mais baixo']):
            return 'min'
        if any(w in question_lower for w in ['quantos', 'quantas', 'quantidade', 'contagem']):
            return 'count'

        return 'list'  # Padrão: listar registros

    @classmethod
    def _detect_category_filter(cls, question: str, module: str) -> Optional[str]:
        """Detecta filtro de categoria baseado no módulo."""
        question_lower = question.lower()

        # Categorias de despesas
        expense_categories = {
            'alimentação': 'food and drink', 'comida': 'food and drink',
            'restaurante': 'food and drink', 'supermercado': 'supermarket',
            'mercado': 'supermarket', 'transporte': 'transport',
            'uber': 'transport', '99': 'transport', 'ônibus': 'transport',
            'metrô': 'transport', 'saúde': 'health and care',
            'farmácia': 'health and care', 'médico': 'health and care',
            'educação': 'education', 'curso': 'education',
            'streaming': 'digital signs', 'netflix': 'digital signs',
            'spotify': 'digital signs', 'amazon': 'digital signs',
            'entretenimento': 'entertainment', 'lazer': 'entertainment',
            'viagem': 'travels', 'hotel': 'travels', 'passagem': 'travels',
            'roupa': 'vestuary', 'vestuário': 'vestuary', 'casa': 'house',
            'aluguel': 'house', 'condomínio': 'bills and services',
            'luz': 'bills and services', 'água': 'bills and services',
            'internet': 'bills and services', 'telefone': 'bills and services'
        }

        # Categorias de receitas
        revenue_categories = {
            'salário': 'salary', 'pagamento': 'salary',
            'freelance': 'income', 'rendimento': 'income',
            'dividendo': 'income', 'reembolso': 'refund',
            'cashback': 'cashback', 'prêmio': 'award',
            'bônus': 'award', 'vale': 'ticket'
        }

        # Categorias de livros
        book_genres = {
            'filosofia': 'Philosophy', 'história': 'History',
            'psicologia': 'Psychology', 'ficção': 'Fiction',
            'política': 'Policy', 'tecnologia': 'Technology',
            'teologia': 'Theology'
        }

        # Categorias de tarefas
        task_categories = {
            'saúde': 'health', 'estudos': 'studies', 'estudo': 'studies',
            'espiritual': 'spiritual', 'exercício': 'exercise',
            'academia': 'exercise', 'meditação': 'meditation',
            'leitura': 'reading', 'trabalho': 'work',
            'família': 'family', 'casa': 'household'
        }

        categories = {}
        if module == 'expenses':
            categories = expense_categories
        elif module == 'revenues':
            categories = revenue_categories
        elif module == 'library':
            categories = book_genres
        elif module == 'personal_planning':
            categories = task_categories

        for keyword, category in categories.items():
            if keyword in question_lower:
                return category

        return None

    @classmethod
    def interpret(cls, question: str, member_id: int) -> QueryResult:
        """
        Interpreta uma pergunta e retorna a query SQL correspondente.

        Args:
            question: Pergunta em português
            member_id: ID do membro para filtrar dados

        Returns:
            QueryResult com SQL, parâmetros e metadados
        """
        module = cls._detect_module(question)
        start_date, end_date, period_desc = cls._get_time_range(question)
        aggregation = cls._detect_aggregation(question)
        category = cls._detect_category_filter(question, module)

        # Delega para o método específico do módulo
        method_name = f'_query_{module}'
        if hasattr(cls, method_name):
            return getattr(cls, method_name)(
                question, member_id, start_date, end_date,
                period_desc, aggregation, category
            )

        return cls._query_unknown(question, member_id)

    @classmethod
    def _query_revenues(
        cls, question: str, member_id: int,
        start_date: Optional[date], end_date: Optional[date],
        period_desc: str, aggregation: str, category: Optional[str]
    ) -> QueryResult:
        """Gera query para módulo de receitas."""
        base_conditions = "deleted_at IS NULL"
        params: List[Any] = []

        if start_date and end_date:
            base_conditions += " AND date BETWEEN %s AND %s"
            params.extend([start_date, end_date])

        if category:
            base_conditions += " AND category = %s"
            params.append(category)

        if aggregation == 'sum':
            sql = f"""
                SELECT
                    COALESCE(SUM(value), 0) as total,
                    COUNT(*) as quantidade
                FROM revenues_revenue
                WHERE {base_conditions}
            """
            display_type = 'currency'
            description = f"Total de receitas {period_desc}"
        elif aggregation == 'avg':
            sql = f"""
                SELECT
                    COALESCE(AVG(value), 0) as media,
                    COUNT(*) as quantidade
                FROM revenues_revenue
                WHERE {base_conditions}
            """
            display_type = 'currency'
            description = f"Média de receitas {period_desc}"
        elif aggregation == 'count':
            sql = f"""
                SELECT
                    COUNT(*) as quantidade,
                    COALESCE(SUM(value), 0) as total
                FROM revenues_revenue
                WHERE {base_conditions}
            """
            display_type = 'text'
            description = f"Quantidade de receitas {period_desc}"
        else:
            sql = f"""
                SELECT
                    description,
                    value,
                    date,
                    category
                FROM revenues_revenue
                WHERE {base_conditions}
                ORDER BY date DESC
                LIMIT 10
            """
            display_type = 'table'
            description = f"Últimas receitas {period_desc}"

        return QueryResult(
            module='revenues',
            sql=sql,
            params=tuple(params),
            display_type=display_type,
            description=description
        )

    @classmethod
    def _query_expenses(
        cls, question: str, member_id: int,
        start_date: Optional[date], end_date: Optional[date],
        period_desc: str, aggregation: str, category: Optional[str]
    ) -> QueryResult:
        """Gera query para módulo de despesas."""
        base_conditions = "deleted_at IS NULL"
        params: List[Any] = []

        if start_date and end_date:
            base_conditions += " AND date BETWEEN %s AND %s"
            params.extend([start_date, end_date])

        if category:
            base_conditions += " AND category = %s"
            params.append(category)

        if aggregation == 'sum':
            sql = f"""
                SELECT
                    COALESCE(SUM(value), 0) as total,
                    COUNT(*) as quantidade
                FROM expenses_expense
                WHERE {base_conditions}
            """
            display_type = 'currency'
            description = f"Total de despesas {period_desc}"
        elif aggregation == 'avg':
            sql = f"""
                SELECT
                    COALESCE(AVG(value), 0) as media,
                    COUNT(*) as quantidade
                FROM expenses_expense
                WHERE {base_conditions}
            """
            display_type = 'currency'
            description = f"Média de despesas {period_desc}"
        elif aggregation == 'count':
            sql = f"""
                SELECT
                    COUNT(*) as quantidade,
                    COALESCE(SUM(value), 0) as total
                FROM expenses_expense
                WHERE {base_conditions}
            """
            display_type = 'text'
            description = f"Quantidade de despesas {period_desc}"
        else:
            # Listar por categoria
            if 'categoria' in question.lower() or 'categorias' in question.lower():
                sql = f"""
                    SELECT
                        category as categoria,
                        COUNT(*) as quantidade,
                        SUM(value) as total
                    FROM expenses_expense
                    WHERE {base_conditions}
                    GROUP BY category
                    ORDER BY total DESC
                """
                display_type = 'table'
                description = f"Despesas por categoria {period_desc}"
            else:
                sql = f"""
                    SELECT
                        description as descricao,
                        value as valor,
                        date as data,
                        category as categoria
                    FROM expenses_expense
                    WHERE {base_conditions}
                    ORDER BY date DESC
                    LIMIT 10
                """
                display_type = 'table'
                description = f"Últimas despesas {period_desc}"

        return QueryResult(
            module='expenses',
            sql=sql,
            params=tuple(params),
            display_type=display_type,
            description=description
        )

    @classmethod
    def _query_accounts(
        cls, question: str, member_id: int,
        start_date: Optional[date], end_date: Optional[date],
        period_desc: str, aggregation: str, category: Optional[str]
    ) -> QueryResult:
        """Gera query para módulo de contas bancárias."""
        question_lower = question.lower()

        # Saldo total
        if any(w in question_lower for w in ['total', 'soma', 'todos', 'todas']):
            sql = """
                SELECT
                    COALESCE(SUM(current_balance), 0) as saldo_total,
                    COUNT(*) as quantidade_contas
                FROM accounts_account
                WHERE deleted_at IS NULL AND is_active = true
            """
            display_type = 'currency'
            description = "Saldo total de todas as contas"
        else:
            sql = """
                SELECT
                    account_name as conta,
                    institution_name as banco,
                    account_type as tipo,
                    current_balance as saldo
                FROM accounts_account
                WHERE deleted_at IS NULL AND is_active = true
                ORDER BY current_balance DESC
            """
            display_type = 'table'
            description = "Saldo das contas bancárias"

        return QueryResult(
            module='accounts',
            sql=sql,
            params=(),
            display_type=display_type,
            description=description
        )

    @classmethod
    def _query_credit_cards(
        cls, question: str, member_id: int,
        start_date: Optional[date], end_date: Optional[date],
        period_desc: str, aggregation: str, category: Optional[str]
    ) -> QueryResult:
        """Gera query para módulo de cartões de crédito."""
        question_lower = question.lower()

        # Limite disponível
        if any(w in question_lower for w in ['limite', 'disponível', 'disponivel']):
            sql = """
                SELECT
                    name as cartao,
                    flag as bandeira,
                    credit_limit as limite_total,
                    (credit_limit - COALESCE(
                        (SELECT SUM(value) FROM credit_cards_creditcardexpense
                         WHERE card_id = credit_cards_creditcard.id
                         AND payed = false AND deleted_at IS NULL), 0
                    )) as limite_disponivel
                FROM credit_cards_creditcard
                WHERE deleted_at IS NULL AND is_active = true
            """
            display_type = 'table'
            description = "Limite disponível dos cartões"
        # Fatura
        elif any(w in question_lower for w in ['fatura', 'faturas']):
            sql = """
                SELECT
                    cc.name as cartao,
                    b.month as mes,
                    b.year as ano,
                    b.total_amount as valor_fatura,
                    b.status
                FROM credit_cards_creditcardbill b
                JOIN credit_cards_creditcard cc ON cc.id = b.credit_card_id
                WHERE b.deleted_at IS NULL
                ORDER BY b.year DESC, b.month DESC
                LIMIT 5
            """
            display_type = 'table'
            description = "Últimas faturas dos cartões"
        else:
            sql = """
                SELECT
                    name as cartao,
                    flag as bandeira,
                    credit_limit as limite,
                    due_day as dia_vencimento,
                    closing_day as dia_fechamento
                FROM credit_cards_creditcard
                WHERE deleted_at IS NULL AND is_active = true
            """
            display_type = 'table'
            description = "Cartões de crédito cadastrados"

        return QueryResult(
            module='credit_cards',
            sql=sql,
            params=(),
            display_type=display_type,
            description=description
        )

    @classmethod
    def _query_loans(
        cls, question: str, member_id: int,
        start_date: Optional[date], end_date: Optional[date],
        period_desc: str, aggregation: str, category: Optional[str]
    ) -> QueryResult:
        """Gera query para módulo de empréstimos."""
        question_lower = question.lower()

        # O que eu devo (empréstimos que peguei)
        if any(w in question_lower for w in ['devo', 'devendo', 'paguei', 'pegar']):
            sql = """
                SELECT
                    l.description as descricao,
                    l.value as valor_total,
                    l.payed_value as valor_pago,
                    (l.value - l.payed_value) as valor_restante,
                    m.name as credor,
                    l.status
                FROM loans_loan l
                LEFT JOIN members_member m ON m.id = l.creditor_id
                WHERE l.deleted_at IS NULL
                    AND l.category = 'borrowed'
                    AND l.status != 'paid'
                ORDER BY l.date DESC
            """
            description = "Empréstimos que você deve"
        # O que me devem (empréstimos que fiz)
        elif any(w in question_lower for w in ['me devem', 'emprestei', 'emprestar']):
            sql = """
                SELECT
                    l.description as descricao,
                    l.value as valor_total,
                    l.payed_value as valor_recebido,
                    (l.value - l.payed_value) as valor_a_receber,
                    m.name as devedor,
                    l.status
                FROM loans_loan l
                LEFT JOIN members_member m ON m.id = l.benefited_id
                WHERE l.deleted_at IS NULL
                    AND l.category = 'lent'
                    AND l.status != 'paid'
                ORDER BY l.date DESC
            """
            description = "Empréstimos que você fez"
        else:
            sql = """
                SELECT
                    l.description as descricao,
                    l.value as valor,
                    l.category as tipo,
                    l.status,
                    l.date as data
                FROM loans_loan l
                WHERE l.deleted_at IS NULL
                ORDER BY l.date DESC
                LIMIT 10
            """
            description = "Últimos empréstimos"

        return QueryResult(
            module='loans',
            sql=sql,
            params=(),
            display_type='table',
            description=description
        )

    @classmethod
    def _query_library(
        cls, question: str, member_id: int,
        start_date: Optional[date], end_date: Optional[date],
        period_desc: str, aggregation: str, category: Optional[str]
    ) -> QueryResult:
        """Gera query para módulo de biblioteca."""
        question_lower = question.lower()
        params: List[Any] = [member_id]

        # Livros que estou lendo
        if any(w in question_lower for w in ['lendo', 'estou lendo', 'leio']):
            sql = """
                SELECT
                    b.title as titulo,
                    b.pages as paginas,
                    b.genre as genero,
                    b.read_status as status,
                    COALESCE(SUM(r.pages_read), 0) as paginas_lidas
                FROM library_book b
                LEFT JOIN library_reading r ON r.book_id = b.id AND r.deleted_at IS NULL
                WHERE b.deleted_at IS NULL
                    AND b.owner_id = %s
                    AND b.read_status = 'reading'
                GROUP BY b.id, b.title, b.pages, b.genre, b.read_status
            """
            description = "Livros que você está lendo"
        # Quantos livros li
        elif any(w in question_lower for w in ['quantos livros li', 'livros lidos', 'já li', 'ja li']):
            sql = """
                SELECT
                    COUNT(*) as quantidade,
                    COALESCE(SUM(pages), 0) as total_paginas
                FROM library_book
                WHERE deleted_at IS NULL
                    AND owner_id = %s
                    AND read_status = 'read'
            """
            display_type = 'text'
            description = "Livros que você já leu"
            return QueryResult(
                module='library',
                sql=sql,
                params=tuple(params),
                display_type=display_type,
                description=description
            )
        # Leituras recentes
        elif any(w in question_lower for w in ['leitura', 'leituras', 'li recente']):
            if start_date and end_date:
                sql = """
                    SELECT
                        b.title as livro,
                        r.reading_date as data,
                        r.pages_read as paginas,
                        r.reading_time as minutos
                    FROM library_reading r
                    JOIN library_book b ON b.id = r.book_id
                    WHERE r.deleted_at IS NULL
                        AND r.owner_id = %s
                        AND r.reading_date BETWEEN %s AND %s
                    ORDER BY r.reading_date DESC
                """
                params.extend([start_date, end_date])
            else:
                sql = """
                    SELECT
                        b.title as livro,
                        r.reading_date as data,
                        r.pages_read as paginas,
                        r.reading_time as minutos
                    FROM library_reading r
                    JOIN library_book b ON b.id = r.book_id
                    WHERE r.deleted_at IS NULL
                        AND r.owner_id = %s
                    ORDER BY r.reading_date DESC
                    LIMIT 10
                """
            description = f"Sessões de leitura {period_desc}"
        else:
            # Lista de livros
            sql = """
                SELECT
                    title as titulo,
                    genre as genero,
                    pages as paginas,
                    read_status as status,
                    rating as avaliacao
                FROM library_book
                WHERE deleted_at IS NULL AND owner_id = %s
                ORDER BY created_at DESC
                LIMIT 10
            """
            description = "Seus livros"

        return QueryResult(
            module='library',
            sql=sql,
            params=tuple(params),
            display_type='table',
            description=description
        )

    @classmethod
    def _query_personal_planning(
        cls, question: str, member_id: int,
        start_date: Optional[date], end_date: Optional[date],
        period_desc: str, aggregation: str, category: Optional[str]
    ) -> QueryResult:
        """Gera query para módulo de planejamento pessoal."""
        question_lower = question.lower()
        today = timezone.now().date()
        params: List[Any] = [member_id]

        # Tarefas de hoje
        if any(w in question_lower for w in ['hoje', 'dia', 'agora']):
            sql = """
                SELECT
                    task_name as tarefa,
                    category as categoria,
                    scheduled_time as horario,
                    status,
                    target_quantity as meta,
                    quantity_completed as realizado
                FROM personal_planning_taskinstance
                WHERE deleted_at IS NULL
                    AND owner_id = %s
                    AND scheduled_date = %s
                ORDER BY scheduled_time NULLS LAST, task_name
            """
            params.append(today)
            description = "Suas tarefas de hoje"
        # Tarefas pendentes
        elif any(w in question_lower for w in ['pendente', 'pendentes', 'falta', 'faltam']):
            sql = """
                SELECT
                    task_name as tarefa,
                    category as categoria,
                    scheduled_date as data,
                    status
                FROM personal_planning_taskinstance
                WHERE deleted_at IS NULL
                    AND owner_id = %s
                    AND status IN ('pending', 'in_progress')
                    AND scheduled_date <= %s
                ORDER BY scheduled_date, scheduled_time NULLS LAST
                LIMIT 15
            """
            params.append(today)
            description = "Suas tarefas pendentes"
        # Objetivos/metas
        elif any(w in question_lower for w in ['objetivo', 'objetivos', 'meta', 'metas', 'goal']):
            sql = """
                SELECT
                    title as objetivo,
                    goal_type as tipo,
                    target_value as meta,
                    current_value as atual,
                    status,
                    start_date as inicio
                FROM personal_planning_goal
                WHERE deleted_at IS NULL
                    AND owner_id = %s
                    AND status = 'active'
                ORDER BY created_at DESC
            """
            description = "Seus objetivos ativos"
        # Taxa de conclusão
        elif any(w in question_lower for w in ['conclusão', 'conclusao', 'concluí', 'conclui', 'completei']):
            sql = """
                SELECT
                    COUNT(*) FILTER (WHERE status = 'completed') as concluidas,
                    COUNT(*) as total,
                    ROUND(
                        COUNT(*) FILTER (WHERE status = 'completed')::numeric / NULLIF(COUNT(*), 0) * 100,
                        1
                    ) as taxa_conclusao
                FROM personal_planning_taskinstance
                WHERE deleted_at IS NULL
                    AND owner_id = %s
                    AND scheduled_date >= %s
            """
            params.append(today - timedelta(days=7))
            display_type = 'text'
            description = "Taxa de conclusão (últimos 7 dias)"
            return QueryResult(
                module='personal_planning',
                sql=sql,
                params=tuple(params),
                display_type=display_type,
                description=description
            )
        else:
            # Tarefas rotineiras ativas
            sql = """
                SELECT
                    name as tarefa,
                    category as categoria,
                    periodicity as periodicidade,
                    target_quantity as quantidade,
                    unit as unidade,
                    is_active as ativa
                FROM personal_planning_routinetask
                WHERE deleted_at IS NULL
                    AND owner_id = %s
                    AND is_active = true
                ORDER BY category, name
            """
            description = "Suas tarefas rotineiras ativas"

        return QueryResult(
            module='personal_planning',
            sql=sql,
            params=tuple(params),
            display_type='table',
            description=description
        )

    @classmethod
    def _query_security(
        cls, question: str, member_id: int,
        start_date: Optional[date], end_date: Optional[date],
        period_desc: str, aggregation: str, category: Optional[str]
    ) -> QueryResult:
        """
        Gera query para módulo de segurança (senhas).

        IMPORTANTE: Retorna dados criptografados que precisam de decriptação.
        """
        question_lower = question.lower()
        params: List[Any] = [member_id]

        # Busca por site específico
        sites = [
            'netflix', 'spotify', 'amazon', 'google', 'facebook',
            'instagram', 'twitter', 'linkedin', 'github', 'microsoft',
            'apple', 'adobe', 'dropbox', 'gmail', 'outlook', 'nubank',
            'itau', 'itaú', 'bradesco', 'santander', 'caixa', 'bb',
            'inter', 'c6', 'picpay', 'mercadopago', 'mercado pago'
        ]

        site_filter = None
        for site in sites:
            if site in question_lower:
                site_filter = site
                break

        if site_filter:
            sql = """
                SELECT
                    id,
                    title as titulo,
                    site,
                    username as usuario,
                    _password as senha_criptografada,
                    category as categoria
                FROM security_password
                WHERE deleted_at IS NULL
                    AND owner_id = %s
                    AND (LOWER(title) LIKE %s OR LOWER(site) LIKE %s)
                LIMIT 5
            """
            search_term = f'%{site_filter}%'
            params.extend([search_term, search_term])
            description = f"Senha para {site_filter}"
        else:
            # Lista de senhas (sem revelar)
            sql = """
                SELECT
                    id,
                    title as titulo,
                    site,
                    username as usuario,
                    _password as senha_criptografada,
                    category as categoria,
                    last_password_change as ultima_alteracao
                FROM security_password
                WHERE deleted_at IS NULL
                    AND owner_id = %s
                ORDER BY title
                LIMIT 10
            """
            description = "Suas senhas armazenadas"

        return QueryResult(
            module='security',
            sql=sql,
            params=tuple(params),
            display_type='password',
            description=description,
            requires_decryption=True,
            decryption_fields=['senha_criptografada']
        )

    @classmethod
    def _query_vaults(
        cls, question: str, member_id: int,
        start_date: Optional[date], end_date: Optional[date],
        period_desc: str, aggregation: str, category: Optional[str]
    ) -> QueryResult:
        """Gera query para módulo de cofres."""
        question_lower = question.lower()

        # Total em cofres
        if any(w in question_lower for w in ['total', 'soma', 'quanto tenho guardado']):
            sql = """
                SELECT
                    COALESCE(SUM(current_balance), 0) as total_guardado,
                    COALESCE(SUM(accumulated_yield), 0) as total_rendimentos,
                    COUNT(*) as quantidade_cofres
                FROM vaults_vault
                WHERE deleted_at IS NULL AND is_active = true
            """
            display_type = 'currency'
            description = "Total em cofres"
        else:
            sql = """
                SELECT
                    v.description as cofre,
                    a.account_name as conta,
                    v.current_balance as saldo,
                    v.accumulated_yield as rendimentos,
                    v.yield_rate as taxa_rendimento
                FROM vaults_vault v
                JOIN accounts_account a ON a.id = v.account_id
                WHERE v.deleted_at IS NULL AND v.is_active = true
                ORDER BY v.current_balance DESC
            """
            display_type = 'table'
            description = "Seus cofres"

        return QueryResult(
            module='vaults',
            sql=sql,
            params=(),
            display_type=display_type,
            description=description
        )

    @classmethod
    def _query_transfers(
        cls, question: str, member_id: int,
        start_date: Optional[date], end_date: Optional[date],
        period_desc: str, aggregation: str, category: Optional[str]
    ) -> QueryResult:
        """Gera query para módulo de transferências."""
        base_conditions = "t.deleted_at IS NULL"
        params: List[Any] = []

        if start_date and end_date:
            base_conditions += " AND t.date BETWEEN %s AND %s"
            params.extend([start_date, end_date])

        if aggregation == 'sum':
            sql = f"""
                SELECT
                    COALESCE(SUM(t.value), 0) as total_transferido,
                    COUNT(*) as quantidade
                FROM transfers_transfer t
                WHERE {base_conditions}
            """
            display_type = 'currency'
            description = f"Total transferido {period_desc}"
        else:
            sql = f"""
                SELECT
                    t.description as descricao,
                    t.value as valor,
                    t.date as data,
                    o.account_name as origem,
                    d.account_name as destino
                FROM transfers_transfer t
                LEFT JOIN accounts_account o ON o.id = t.origin_account_id
                LEFT JOIN accounts_account d ON d.id = t.destiny_account_id
                WHERE {base_conditions}
                ORDER BY t.date DESC
                LIMIT 10
            """
            display_type = 'table'
            description = f"Últimas transferências {period_desc}"

        return QueryResult(
            module='transfers',
            sql=sql,
            params=tuple(params),
            display_type=display_type,
            description=description
        )

    @classmethod
    def _query_unknown(cls, question: str, member_id: int) -> QueryResult:
        """Query padrão quando não consegue identificar o módulo."""
        return QueryResult(
            module='unknown',
            sql='',
            params=(),
            display_type='text',
            description='Não consegui identificar sobre o que você está perguntando.'
        )
