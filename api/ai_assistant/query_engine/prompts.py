"""
SQL Generation Prompts for AI Assistant.

Contains system and user prompts for LLM-based SQL generation.
"""

from datetime import date, datetime
from typing import Optional


def get_current_date_context() -> str:
    """Get current date context for temporal queries."""
    today = date.today()
    return f"""
DATA ATUAL: {today.strftime('%Y-%m-%d')} ({today.strftime('%d/%m/%Y')})
ANO ATUAL: {today.year}
MES ATUAL: {today.month}
DIA ATUAL: {today.day}
"""


SQL_GENERATION_SYSTEM_PROMPT = """Voce e um especialista em SQL PostgreSQL para o sistema PersonalHub.
Sua tarefa e gerar consultas SQL seguras e precisas baseadas em perguntas em linguagem natural.

{date_context}

## REGRAS CRITICAS DE SEGURANCA

1. **APENAS SELECT**: Nunca gere INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, GRANT, REVOKE
2. **SOFT DELETE**: Sempre inclua `deleted_at IS NULL` ou `is_deleted = false` para tabelas com soft delete
3. **OWNER FILTER**: O filtro de owner sera injetado automaticamente - NAO inclua na query
4. **SEM CAMPOS SENSIVEIS**: NUNCA selecione campos que comecam com underscore (_password, _card_number, etc.)
5. **SEM LIMIT POR PADRAO**: Nao adicione LIMIT a menos que o usuario peca explicitamente

## REGRAS DE FORMATACAO

1. Use nomes de tabela do PostgreSQL (snake_case): `expenses_expense`, `library_book`, etc.
2. Datas no formato ISO: 'YYYY-MM-DD'
3. Para periodos:
   - "esse mes" = >= primeiro dia do mes atual AND <= ultimo dia do mes atual
   - "janeiro" = >= '2026-01-01' AND <= '2026-01-31' (use o ano atual)
   - "ultimo mes" = mes anterior ao atual
   - "esse ano" = >= primeiro dia do ano atual
4. Para agregacoes monetarias, use SUM(value) e formate como decimal
5. Para agrupamentos temporais, use DATE_TRUNC('month', date) ou DATE_TRUNC('day', date)

## SCHEMA DO BANCO DE DADOS

{schema}

## EXEMPLOS DE QUERIES

### Despesas

Pergunta: "Quanto gastei esse mes?"
```sql
SELECT SUM(value) as total
FROM expenses_expense
WHERE date >= DATE_TRUNC('month', CURRENT_DATE)
  AND date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
  AND deleted_at IS NULL
```

Pergunta: "Despesas por categoria esse mes"
```sql
SELECT category, SUM(value) as total, COUNT(*) as quantidade
FROM expenses_expense
WHERE date >= DATE_TRUNC('month', CURRENT_DATE)
  AND date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
  AND deleted_at IS NULL
GROUP BY category
ORDER BY total DESC
```

Pergunta: "Maiores despesas de janeiro"
```sql
SELECT description, value, category, date
FROM expenses_expense
WHERE date >= '2026-01-01' AND date <= '2026-01-31'
  AND deleted_at IS NULL
ORDER BY value DESC
```

Pergunta: "Evolucao mensal das despesas"
```sql
SELECT DATE_TRUNC('month', date) as mes, SUM(value) as total
FROM expenses_expense
WHERE date >= DATE_TRUNC('year', CURRENT_DATE)
  AND deleted_at IS NULL
GROUP BY DATE_TRUNC('month', date)
ORDER BY mes
```

### Receitas

Pergunta: "Quanto recebi esse mes?"
```sql
SELECT SUM(value) as total
FROM revenues_revenue
WHERE date >= DATE_TRUNC('month', CURRENT_DATE)
  AND date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
  AND deleted_at IS NULL
```

Pergunta: "Receitas por fonte"
```sql
SELECT category, source, SUM(value) as total
FROM revenues_revenue
WHERE date >= DATE_TRUNC('month', CURRENT_DATE)
  AND deleted_at IS NULL
GROUP BY category, source
ORDER BY total DESC
```

### Livros

Pergunta: "Quais livros estou lendo?"
```sql
SELECT title, pages, genre, rating
FROM library_book
WHERE read_status = 'reading'
  AND deleted_at IS NULL
ORDER BY updated_at DESC
```

Pergunta: "Quantos livros li esse ano?"
```sql
SELECT COUNT(*) as total
FROM library_book
WHERE read_status = 'read'
  AND deleted_at IS NULL
```

Pergunta: "Livros por genero"
```sql
SELECT genre, COUNT(*) as quantidade
FROM library_book
WHERE deleted_at IS NULL
GROUP BY genre
ORDER BY quantidade DESC
```

### Leituras

Pergunta: "Quantas paginas li hoje?"
```sql
SELECT SUM(pages_read) as total_paginas, SUM(reading_time) as total_minutos
FROM library_reading
WHERE reading_date = CURRENT_DATE
  AND deleted_at IS NULL
```

Pergunta: "Historico de leitura desse mes"
```sql
SELECT r.reading_date, b.title, r.pages_read, r.reading_time
FROM library_reading r
JOIN library_book b ON r.book_id = b.id
WHERE r.reading_date >= DATE_TRUNC('month', CURRENT_DATE)
  AND r.deleted_at IS NULL
  AND b.deleted_at IS NULL
ORDER BY r.reading_date DESC
```

### Contas e Saldos

Pergunta: "Saldo das minhas contas"
```sql
SELECT account_name, institution_name, current_balance, account_type
FROM accounts_account
WHERE is_active = true
  AND deleted_at IS NULL
ORDER BY current_balance DESC
```

Pergunta: "Saldo total"
```sql
SELECT SUM(current_balance) as saldo_total
FROM accounts_account
WHERE is_active = true
  AND deleted_at IS NULL
```

### Metas e Planejamento

Pergunta: "Minhas metas ativas"
```sql
SELECT title, goal_type, target_value, current_value, start_date, status
FROM personal_planning_goal
WHERE status = 'active'
  AND deleted_at IS NULL
ORDER BY start_date DESC
```

Pergunta: "Tarefas de hoje"
```sql
SELECT task_name, category, scheduled_time, status, target_quantity, quantity_completed
FROM personal_planning_taskinstance
WHERE scheduled_date = CURRENT_DATE
  AND deleted_at IS NULL
ORDER BY scheduled_time NULLS LAST
```

### Emprestimos

Pergunta: "Emprestimos ativos"
```sql
SELECT description, value, payed_value, (value - payed_value) as saldo_devedor,
       date, due_date, status
FROM loans_loan
WHERE status = 'active'
  AND deleted_at IS NULL
ORDER BY due_date NULLS LAST
```

### Senhas (apenas metadados)

Pergunta: "Minhas senhas salvas"
```sql
SELECT title, site, username, category, last_password_change
FROM security_password
WHERE deleted_at IS NULL
ORDER BY title
```

## FORMATO DE RESPOSTA

Responda APENAS com o SQL, sem explicacoes adicionais. O SQL deve:
1. Ser valido para PostgreSQL
2. Estar pronto para execucao (sem placeholders)
3. Incluir aliases descritivos para colunas calculadas
4. Usar JOINs quando necessario para trazer informacoes relacionadas
"""


SQL_ANSWER_GENERATION_PROMPT = """Voce e o assistente do PersonalHub. Com base nos resultados da consulta SQL,
gere uma resposta clara e informativa em portugues.

## REGRAS

1. **Precisao**: Use APENAS os dados retornados - NUNCA invente ou complete dados ausentes
2. **Formatacao de valores**:
   - Monetarios: R$ X.XXX,XX (com ponto para milhar e virgula para decimal)
   - Datas: DD/MM/AAAA
   - Porcentagens: XX,XX%
3. **Estrutura da resposta**:
   - Comece com um resumo direto respondendo a pergunta
   - Liste os dados relevantes (tabela se houver multiplos registros)
   - Inclua totais e agregacoes quando aplicavel
4. **Se nao houver resultados**: Diga claramente que nao foram encontrados dados
5. **Markdown**: Use formatacao markdown para melhor legibilidade

## DADOS DA CONSULTA

Pergunta do usuario: {question}

SQL executado:
```sql
{sql}
```

Resultado ({row_count} registro(s)):
{results}

## FORMATO OBRIGATORIO DA RESPOSTA

Sua resposta DEVE terminar com a secao SQL:

```
[Sua resposta aqui]

---
### SQL Executado
```sql
{sql}
```
```

Agora, gere a resposta:
"""


def get_sql_generation_prompt(schema_text: str) -> str:
    """
    Generate the complete SQL generation system prompt.

    Args:
        schema_text: Formatted schema description from SchemaService

    Returns:
        Complete system prompt for SQL generation
    """
    return SQL_GENERATION_SYSTEM_PROMPT.format(
        date_context=get_current_date_context(),
        schema=schema_text
    )


def get_answer_generation_prompt(
    question: str,
    sql: str,
    results: str,
    row_count: int
) -> str:
    """
    Generate the prompt for answer generation from SQL results.

    Args:
        question: Original user question
        sql: Executed SQL query
        results: Formatted query results
        row_count: Number of rows returned

    Returns:
        Complete prompt for answer generation
    """
    return SQL_ANSWER_GENERATION_PROMPT.format(
        question=question,
        sql=sql,
        results=results,
        row_count=row_count
    )


# ============================================================================
# QUERY TYPE DETECTION
# ============================================================================

QUERY_TYPE_INDICATORS = {
    'aggregation': [
        'total', 'quanto', 'quantos', 'quantas', 'soma', 'somatorio',
        'media', 'média', 'maior', 'menor', 'maximo', 'minimo',
        'count', 'sum', 'avg', 'max', 'min'
    ],
    'listing': [
        'liste', 'listar', 'mostre', 'mostrar', 'exiba', 'exibir',
        'quais', 'todos', 'todas', 'ultimos', 'ultimas', 'recentes',
        'list', 'show', 'display'
    ],
    'trend': [
        'evolucao', 'evolução', 'historico', 'histórico', 'tendencia',
        'tendência', 'ao longo', 'por mes', 'por mês', 'mensal',
        'semanal', 'diario', 'diário', 'timeline', 'trend'
    ],
    'comparison': [
        'compare', 'comparar', 'comparacao', 'comparação', 'versus',
        'vs', 'diferenca', 'diferença', 'entre'
    ],
    'lookup': [
        'qual', 'onde', 'quando', 'quem', 'como', 'encontre', 'ache',
        'busque', 'procure', 'what', 'where', 'when', 'who', 'find'
    ],
}


def detect_query_type(question: str) -> str:
    """
    Detect the type of query from the question.

    Args:
        question: User's question in natural language

    Returns:
        Query type: aggregation, listing, trend, comparison, or lookup
    """
    question_lower = question.lower()

    for query_type, indicators in QUERY_TYPE_INDICATORS.items():
        for indicator in indicators:
            if indicator in question_lower:
                return query_type

    return 'lookup'  # Default


# ============================================================================
# MODULE DETECTION
# ============================================================================

MODULE_INDICATORS = {
    'finance': [
        'despesa', 'gasto', 'gastei', 'gastou', 'expense',
        'receita', 'receb', 'salario', 'salário', 'revenue', 'income',
        'conta', 'saldo', 'banco', 'account', 'balance',
        'cartao', 'cartão', 'fatura', 'credit', 'card',
        'transferencia', 'transferência', 'pix', 'ted', 'transfer',
        'emprestimo', 'empréstimo', 'devo', 'devem', 'loan'
    ],
    'library': [
        'livro', 'book', 'leitura', 'reading', 'pagina', 'página',
        'autor', 'author', 'editora', 'publisher', 'genero', 'gênero',
        'lendo', 'lido', 'ler', 'resumo', 'summary'
    ],
    'security': [
        'senha', 'password', 'credencial', 'login', 'usuario', 'usuário',
        'cofre', 'vault', 'arquivo', 'documento', 'document'
    ],
    'planning': [
        'meta', 'goal', 'tarefa', 'task', 'habito', 'hábito', 'habit',
        'rotina', 'routine', 'reflexao', 'reflexão', 'reflection',
        'humor', 'mood', 'planejamento', 'planning'
    ],
}


def detect_module(question: str) -> str:
    """
    Detect which module the question is about.

    Args:
        question: User's question in natural language

    Returns:
        Module name: finance, library, security, planning, or general
    """
    question_lower = question.lower()

    for module, indicators in MODULE_INDICATORS.items():
        for indicator in indicators:
            if indicator in question_lower:
                return module

    return 'general'
