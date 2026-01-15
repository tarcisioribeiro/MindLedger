"""
Database Schema Definitions for SQL Generation.

Contains complete schema mapping for all PersonalHub models,
including column types, relationships, and query patterns.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ColumnType(Enum):
    """Database column types."""
    INTEGER = 'integer'
    BIGINT = 'bigint'
    VARCHAR = 'varchar'
    TEXT = 'text'
    DECIMAL = 'decimal'
    BOOLEAN = 'boolean'
    DATE = 'date'
    TIME = 'time'
    DATETIME = 'datetime'
    JSON = 'jsonb'
    ARRAY = 'array'
    UUID = 'uuid'


@dataclass
class ColumnDef:
    """Column definition with metadata."""
    name: str
    col_type: ColumnType
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None
    choices: Optional[List[str]] = None
    sensitive: bool = False  # Never return in queries
    searchable: bool = False  # Can be used in text search
    aggregable: bool = False  # Can be summed/averaged
    filterable: bool = True  # Can be used in WHERE
    description: str = ""


# ============================================================================
# EXPENSE CATEGORIES (shared across modules)
# ============================================================================

EXPENSE_CATEGORIES = [
    'food and drink', 'bills and services', 'electronics', 'family and friends',
    'pets', 'digital signs', 'house', 'purchases', 'donate', 'education',
    'loans', 'entertainment', 'taxes', 'investments', 'others', 'vestuary',
    'health and care', 'professional services', 'supermarket', 'rates',
    'transport', 'travels'
]

REVENUE_CATEGORIES = [
    'deposit', 'award', 'salary', 'ticket', 'income', 'refund',
    'cashback', 'transfer', 'received_loan', 'loan_devolution'
]

PAYMENT_METHODS = [
    'cash', 'debit_card', 'credit_card', 'pix', 'transfer', 'check', 'other'
]

PAYMENT_FREQUENCIES = [
    'daily', 'weekly', 'monthly', 'quarterly', 'semiannual', 'annual'
]

LOAN_STATUSES = ['active', 'paid', 'overdue', 'cancelled']
BILL_STATUSES = ['open', 'closed', 'paid', 'overdue']
BOOK_READ_STATUSES = ['to_read', 'reading', 'read']
BOOK_GENRES = ['Philosophy', 'History', 'Psychology', 'Fiction', 'Policy', 'Technology', 'Theology']
BOOK_LANGUAGES = ['Por', 'Ing', 'Esp']
BOOK_MEDIA_TYPES = ['Dig', 'Phi']
TASK_STATUSES = ['pending', 'in_progress', 'completed', 'skipped', 'cancelled']
GOAL_STATUSES = ['active', 'completed', 'failed', 'cancelled']
MOOD_CHOICES = ['excellent', 'good', 'neutral', 'bad', 'terrible']


# ============================================================================
# MODELS SCHEMA - Complete database structure
# ============================================================================

MODELS_SCHEMA: Dict[str, Dict[str, Any]] = {
    # ========================================================================
    # LIBRARY MODULE
    # ========================================================================
    'library_book': {
        'description': 'Livros da biblioteca pessoal',
        'description_en': 'Personal library books',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'uuid': {'type': 'uuid'},
            'title': {'type': 'varchar(200)', 'searchable': True, 'description': 'Titulo do livro'},
            'pages': {'type': 'integer', 'aggregable': True, 'description': 'Numero de paginas'},
            'language': {'type': 'varchar(10)', 'choices': BOOK_LANGUAGES, 'description': 'Idioma'},
            'genre': {'type': 'varchar(50)', 'choices': BOOK_GENRES, 'description': 'Genero literario'},
            'literarytype': {'type': 'varchar(50)', 'choices': ['book', 'collection', 'magazine', 'article', 'essay']},
            'publish_date': {'type': 'date', 'nullable': True},
            'synopsis': {'type': 'text', 'searchable': True},
            'edition': {'type': 'varchar(50)'},
            'media_type': {'type': 'varchar(10)', 'choices': BOOK_MEDIA_TYPES, 'nullable': True},
            'rating': {'type': 'integer', 'nullable': True, 'aggregable': True, 'description': 'Nota de 1 a 5'},
            'read_status': {'type': 'varchar(20)', 'choices': BOOK_READ_STATUSES, 'description': 'Status de leitura'},
            'publisher_id': {'type': 'integer', 'fk': 'library_publisher'},
            'owner_id': {'type': 'integer', 'fk': 'members_member'},
            'created_at': {'type': 'datetime'},
            'updated_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
        'relationships': {
            'publisher': {'table': 'library_publisher', 'type': 'many_to_one'},
            'authors': {'table': 'library_author', 'type': 'many_to_many', 'through': 'library_book_authors'},
            'readings': {'table': 'library_reading', 'type': 'one_to_many'},
        },
        'common_queries': [
            'livros que estou lendo',
            'livros lidos',
            'livros para ler',
            'livros de filosofia',
            'quantos livros tenho',
        ],
    },

    'library_author': {
        'description': 'Autores dos livros',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'name': {'type': 'varchar(200)', 'searchable': True},
            'birth_year': {'type': 'integer', 'nullable': True},
            'birth_era': {'type': 'varchar(5)', 'choices': ['AC', 'DC']},
            'death_year': {'type': 'integer', 'nullable': True},
            'death_era': {'type': 'varchar(5)', 'choices': ['AC', 'DC'], 'nullable': True},
            'nationality': {'type': 'varchar(10)', 'choices': ['USA', 'BRA', 'SUI', 'ALE', 'CZE', 'ISR', 'AUS', 'ROM', 'GRE', 'FRA', 'ING', 'CUB', 'MEX', 'ESP']},
            'biography': {'type': 'text', 'nullable': True, 'searchable': True},
            'owner_id': {'type': 'integer', 'fk': 'members_member'},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
    },

    'library_publisher': {
        'description': 'Editoras dos livros',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'name': {'type': 'varchar(200)', 'searchable': True},
            'description': {'type': 'text', 'nullable': True},
            'website': {'type': 'varchar(200)', 'nullable': True},
            'country': {'type': 'varchar(10)', 'choices': ['BRA', 'USA', 'UK', 'POR'], 'nullable': True},
            'founded_year': {'type': 'integer', 'nullable': True},
            'owner_id': {'type': 'integer', 'fk': 'members_member'},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
    },

    'library_reading': {
        'description': 'Sessoes de leitura registradas',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'book_id': {'type': 'integer', 'fk': 'library_book'},
            'reading_date': {'type': 'date', 'description': 'Data da sessao de leitura'},
            'reading_time': {'type': 'integer', 'aggregable': True, 'description': 'Tempo em minutos'},
            'pages_read': {'type': 'integer', 'aggregable': True, 'description': 'Paginas lidas na sessao'},
            'notes': {'type': 'text', 'nullable': True, 'searchable': True},
            'owner_id': {'type': 'integer', 'fk': 'members_member'},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
        'common_queries': [
            'quantas paginas li hoje',
            'tempo total de leitura',
            'historico de leitura',
            'leituras do mes',
        ],
    },

    'library_summary': {
        'description': 'Resumos de livros',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'title': {'type': 'varchar(200)', 'searchable': True},
            'book_id': {'type': 'integer', 'fk': 'library_book'},
            'text': {'type': 'text', 'searchable': True, 'description': 'Conteudo do resumo em markdown'},
            'is_vectorized': {'type': 'boolean'},
            'vectorization_date': {'type': 'datetime', 'nullable': True},
            'owner_id': {'type': 'integer', 'fk': 'members_member'},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
    },

    # Many-to-many relationship table
    'library_book_authors': {
        'description': 'Relacao livros-autores',
        'owner_field': None,
        'soft_delete': False,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'book_id': {'type': 'integer', 'fk': 'library_book'},
            'author_id': {'type': 'integer', 'fk': 'library_author'},
        },
    },

    # ========================================================================
    # EXPENSES MODULE
    # ========================================================================
    'expenses_expense': {
        'description': 'Despesas e gastos',
        'description_en': 'Expenses and spending',
        'owner_field': 'member_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'uuid': {'type': 'uuid'},
            'description': {'type': 'varchar(100)', 'searchable': True, 'description': 'Descricao da despesa'},
            'value': {'type': 'decimal(10,2)', 'aggregable': True, 'description': 'Valor da despesa'},
            'date': {'type': 'date', 'description': 'Data da despesa'},
            'horary': {'type': 'time'},
            'category': {'type': 'varchar(200)', 'choices': EXPENSE_CATEGORIES, 'description': 'Categoria'},
            'account_id': {'type': 'integer', 'fk': 'accounts_account'},
            'payed': {'type': 'boolean', 'description': 'Se foi paga'},
            'merchant': {'type': 'varchar(200)', 'nullable': True, 'searchable': True},
            'location': {'type': 'varchar(200)', 'nullable': True},
            'payment_method': {'type': 'varchar(50)', 'choices': PAYMENT_METHODS, 'nullable': True},
            'member_id': {'type': 'integer', 'fk': 'members_member', 'nullable': True},
            'notes': {'type': 'text', 'nullable': True, 'searchable': True},
            'recurring': {'type': 'boolean'},
            'frequency': {'type': 'varchar(20)', 'choices': PAYMENT_FREQUENCIES, 'nullable': True},
            'related_transfer_id': {'type': 'integer', 'fk': 'transfers_transfer', 'nullable': True},
            'related_loan_id': {'type': 'integer', 'fk': 'loans_loan', 'nullable': True},
            'fixed_expense_template_id': {'type': 'integer', 'fk': 'expenses_fixedexpense', 'nullable': True},
            'created_at': {'type': 'datetime'},
            'updated_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
        'common_queries': [
            'quanto gastei esse mes',
            'despesas por categoria',
            'maiores despesas',
            'gastos com alimentacao',
            'despesas pendentes',
        ],
    },

    'expenses_fixedexpense': {
        'description': 'Despesas fixas recorrentes',
        'owner_field': 'member_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'description': {'type': 'varchar(200)', 'searchable': True},
            'default_value': {'type': 'decimal(10,2)', 'aggregable': True},
            'category': {'type': 'varchar(200)', 'choices': EXPENSE_CATEGORIES},
            'account_id': {'type': 'integer', 'fk': 'accounts_account', 'nullable': True},
            'credit_card_id': {'type': 'integer', 'fk': 'credit_cards_creditcard', 'nullable': True},
            'due_day': {'type': 'integer', 'description': 'Dia do vencimento (1-31)'},
            'merchant': {'type': 'varchar(200)', 'nullable': True},
            'payment_method': {'type': 'varchar(50)', 'choices': PAYMENT_METHODS, 'nullable': True},
            'notes': {'type': 'text', 'nullable': True},
            'member_id': {'type': 'integer', 'fk': 'members_member', 'nullable': True},
            'is_active': {'type': 'boolean', 'description': 'Se esta ativa'},
            'allow_value_edit': {'type': 'boolean'},
            'last_generated_month': {'type': 'varchar(7)', 'nullable': True},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
    },

    # ========================================================================
    # REVENUES MODULE
    # ========================================================================
    'revenues_revenue': {
        'description': 'Receitas e ganhos',
        'description_en': 'Revenues and income',
        'owner_field': 'member_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'uuid': {'type': 'uuid'},
            'description': {'type': 'varchar(200)', 'searchable': True, 'description': 'Descricao da receita'},
            'value': {'type': 'decimal(10,2)', 'aggregable': True, 'description': 'Valor da receita'},
            'date': {'type': 'date', 'description': 'Data da receita'},
            'horary': {'type': 'time'},
            'category': {'type': 'varchar(200)', 'choices': REVENUE_CATEGORIES, 'description': 'Categoria'},
            'account_id': {'type': 'integer', 'fk': 'accounts_account'},
            'received': {'type': 'boolean', 'description': 'Se foi recebida'},
            'source': {'type': 'varchar(200)', 'nullable': True, 'searchable': True},
            'tax_amount': {'type': 'decimal(10,2)'},
            'net_amount': {'type': 'decimal(10,2)', 'nullable': True, 'aggregable': True},
            'member_id': {'type': 'integer', 'fk': 'members_member', 'nullable': True},
            'notes': {'type': 'text', 'nullable': True},
            'recurring': {'type': 'boolean'},
            'frequency': {'type': 'varchar(20)', 'choices': PAYMENT_FREQUENCIES, 'nullable': True},
            'related_transfer_id': {'type': 'integer', 'fk': 'transfers_transfer', 'nullable': True},
            'related_loan_id': {'type': 'integer', 'fk': 'loans_loan', 'nullable': True},
            'created_at': {'type': 'datetime'},
            'updated_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
        'common_queries': [
            'quanto recebi esse mes',
            'receitas por categoria',
            'salario do mes',
            'total de receitas',
        ],
    },

    # ========================================================================
    # ACCOUNTS MODULE
    # ========================================================================
    'accounts_account': {
        'description': 'Contas bancarias',
        'description_en': 'Bank accounts',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'uuid': {'type': 'uuid'},
            'account_name': {'type': 'varchar(200)', 'searchable': True, 'description': 'Nome da conta'},
            'institution_name': {'type': 'varchar(10)', 'choices': ['NUB', 'SIC', 'MPG', 'IFB', 'CEF'], 'description': 'Banco'},
            'account_type': {'type': 'varchar(5)', 'choices': ['CC', 'CS', 'FG', 'VA'], 'description': 'Tipo de conta'},
            'is_active': {'type': 'boolean', 'description': 'Se esta ativa'},
            '_account_number': {'type': 'text', 'sensitive': True},  # ENCRYPTED - never return
            'agency': {'type': 'varchar(20)', 'nullable': True},
            'bank_code': {'type': 'varchar(10)', 'nullable': True},
            'current_balance': {'type': 'decimal(15,2)', 'aggregable': True, 'description': 'Saldo atual'},
            'minimum_balance': {'type': 'decimal(15,2)'},
            'opening_date': {'type': 'date', 'nullable': True},
            'description': {'type': 'text', 'nullable': True},
            'owner_id': {'type': 'integer', 'fk': 'members_member', 'nullable': True},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
        'common_queries': [
            'saldo das contas',
            'contas ativas',
            'saldo total',
        ],
    },

    # ========================================================================
    # CREDIT CARDS MODULE
    # ========================================================================
    'credit_cards_creditcard': {
        'description': 'Cartoes de credito',
        'description_en': 'Credit cards',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'uuid': {'type': 'uuid'},
            'name': {'type': 'varchar(200)', 'searchable': True, 'description': 'Nome do cartao'},
            'on_card_name': {'type': 'varchar(200)'},
            'flag': {'type': 'varchar(5)', 'choices': ['MSC', 'VSA', 'ELO', 'EXP', 'HCD'], 'description': 'Bandeira'},
            'validation_date': {'type': 'date'},
            '_security_code': {'type': 'text', 'sensitive': True},  # ENCRYPTED
            'credit_limit': {'type': 'decimal(10,2)', 'aggregable': True, 'description': 'Limite de credito'},
            'max_limit': {'type': 'decimal(10,2)'},
            'associated_account_id': {'type': 'integer', 'fk': 'accounts_account'},
            '_card_number': {'type': 'text', 'sensitive': True, 'nullable': True},  # ENCRYPTED
            'is_active': {'type': 'boolean', 'description': 'Se esta ativo'},
            'closing_day': {'type': 'integer', 'nullable': True, 'description': 'Dia de fechamento'},
            'due_day': {'type': 'integer', 'nullable': True, 'description': 'Dia de vencimento'},
            'interest_rate': {'type': 'decimal(5,2)', 'nullable': True},
            'annual_fee': {'type': 'decimal(10,2)', 'nullable': True},
            'owner_id': {'type': 'integer', 'fk': 'members_member', 'nullable': True},
            'notes': {'type': 'text', 'nullable': True},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
    },

    'credit_cards_creditcardbill': {
        'description': 'Faturas de cartao de credito',
        'description_en': 'Credit card bills',
        'owner_field': None,  # Access through credit_card.owner_id
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'credit_card_id': {'type': 'integer', 'fk': 'credit_cards_creditcard'},
            'year': {'type': 'varchar(4)'},
            'month': {'type': 'varchar(3)', 'choices': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']},
            'invoice_beginning_date': {'type': 'date'},
            'invoice_ending_date': {'type': 'date'},
            'closed': {'type': 'boolean'},
            'total_amount': {'type': 'decimal(10,2)', 'aggregable': True, 'description': 'Valor total da fatura'},
            'minimum_payment': {'type': 'decimal(10,2)'},
            'due_date': {'type': 'date', 'nullable': True},
            'paid_amount': {'type': 'decimal(10,2)'},
            'payment_date': {'type': 'date', 'nullable': True},
            'interest_charged': {'type': 'decimal(10,2)'},
            'late_fee': {'type': 'decimal(10,2)'},
            'status': {'type': 'varchar(20)', 'choices': BILL_STATUSES, 'description': 'Status da fatura'},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
    },

    'credit_cards_creditcardexpense': {
        'description': 'Despesas no cartao de credito',
        'description_en': 'Credit card expenses',
        'owner_field': 'member_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'description': {'type': 'varchar(200)', 'searchable': True},
            'value': {'type': 'decimal(10,2)', 'aggregable': True, 'description': 'Valor da despesa'},
            'date': {'type': 'date'},
            'horary': {'type': 'time'},
            'category': {'type': 'varchar(200)', 'choices': EXPENSE_CATEGORIES},
            'card_id': {'type': 'integer', 'fk': 'credit_cards_creditcard'},
            'installment': {'type': 'integer', 'description': 'Parcela atual'},
            'payed': {'type': 'boolean'},
            'total_installments': {'type': 'integer', 'description': 'Total de parcelas'},
            'merchant': {'type': 'varchar(200)', 'nullable': True},
            'transaction_id': {'type': 'varchar(100)', 'nullable': True},
            'location': {'type': 'varchar(200)', 'nullable': True},
            'bill_id': {'type': 'integer', 'fk': 'credit_cards_creditcardbill', 'nullable': True},
            'member_id': {'type': 'integer', 'fk': 'members_member', 'nullable': True},
            'notes': {'type': 'text', 'nullable': True},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
    },

    # ========================================================================
    # TRANSFERS MODULE
    # ========================================================================
    'transfers_transfer': {
        'description': 'Transferencias entre contas',
        'description_en': 'Transfers between accounts',
        'owner_field': 'member_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'uuid': {'type': 'uuid'},
            'description': {'type': 'varchar(200)', 'searchable': True},
            'value': {'type': 'decimal(10,2)', 'aggregable': True, 'description': 'Valor transferido'},
            'date': {'type': 'date'},
            'horary': {'type': 'time'},
            'category': {'type': 'varchar(10)', 'choices': ['doc', 'ted', 'pix']},
            'origin_account_id': {'type': 'integer', 'fk': 'accounts_account'},
            'destiny_account_id': {'type': 'integer', 'fk': 'accounts_account'},
            'transfered': {'type': 'boolean', 'description': 'Se foi efetivada'},
            'transaction_id': {'type': 'varchar(100)', 'nullable': True},
            'fee': {'type': 'decimal(10,2)'},
            'exchange_rate': {'type': 'decimal(10,6)', 'nullable': True},
            'processed_at': {'type': 'datetime', 'nullable': True},
            'confirmation_code': {'type': 'varchar(100)', 'nullable': True},
            'notes': {'type': 'text', 'nullable': True},
            'member_id': {'type': 'integer', 'fk': 'members_member', 'nullable': True},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
    },

    # ========================================================================
    # LOANS MODULE
    # ========================================================================
    'loans_loan': {
        'description': 'Emprestimos concedidos ou recebidos',
        'description_en': 'Loans given or received',
        'owner_field': None,  # Complex: can be benefited_id or creditor_id
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'uuid': {'type': 'uuid'},
            'description': {'type': 'varchar(200)', 'searchable': True},
            'value': {'type': 'decimal(10,2)', 'aggregable': True, 'description': 'Valor total do emprestimo'},
            'payed_value': {'type': 'decimal(10,2)', 'aggregable': True, 'description': 'Valor ja pago'},
            'date': {'type': 'date'},
            'horary': {'type': 'time'},
            'category': {'type': 'varchar(200)', 'choices': EXPENSE_CATEGORIES},
            'account_id': {'type': 'integer', 'fk': 'accounts_account'},
            'benefited_id': {'type': 'integer', 'fk': 'members_member', 'description': 'Quem recebeu o emprestimo'},
            'creditor_id': {'type': 'integer', 'fk': 'members_member', 'description': 'Quem emprestou'},
            'payed': {'type': 'boolean'},
            'interest_rate': {'type': 'decimal(5,2)', 'nullable': True},
            'installments': {'type': 'integer', 'description': 'Numero de parcelas'},
            'due_date': {'type': 'date', 'nullable': True},
            'payment_frequency': {'type': 'varchar(20)', 'choices': PAYMENT_FREQUENCIES},
            'late_fee': {'type': 'decimal(10,2)'},
            'guarantor_id': {'type': 'integer', 'fk': 'members_member', 'nullable': True},
            'notes': {'type': 'text', 'nullable': True},
            'status': {'type': 'varchar(20)', 'choices': LOAN_STATUSES, 'description': 'Status do emprestimo'},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
        'common_queries': [
            'emprestimos ativos',
            'quanto devo',
            'quanto me devem',
            'emprestimos pendentes',
        ],
    },

    # ========================================================================
    # SECURITY MODULE
    # ========================================================================
    'security_password': {
        'description': 'Senhas armazenadas (apenas metadados, nunca a senha)',
        'description_en': 'Stored passwords (metadata only, never the password)',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'title': {'type': 'varchar(200)', 'searchable': True, 'description': 'Nome do servico'},
            'site': {'type': 'varchar(200)', 'description': 'URL do site'},
            'username': {'type': 'varchar(200)', 'description': 'Nome de usuario'},
            '_password': {'type': 'text', 'sensitive': True},  # ENCRYPTED - NEVER return
            'category': {'type': 'varchar(50)', 'choices': ['social', 'email', 'banking', 'work', 'entertainment', 'shopping', 'streaming', 'gaming', 'other']},
            'notes': {'type': 'text', 'nullable': True},
            'last_password_change': {'type': 'datetime'},
            'owner_id': {'type': 'integer', 'fk': 'members_member'},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
        'sensitive_note': 'NUNCA retorne o campo _password. Apenas metadados sao permitidos.',
    },

    'security_storedcreditcard': {
        'description': 'Cartoes armazenados no cofre (apenas metadados)',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'name': {'type': 'varchar(200)', 'searchable': True},
            '_card_number': {'type': 'text', 'sensitive': True},  # ENCRYPTED
            '_security_code': {'type': 'text', 'sensitive': True},  # ENCRYPTED
            'expiration_month': {'type': 'integer'},
            'expiration_year': {'type': 'integer'},
            'cardholder_name': {'type': 'varchar(200)'},
            'flag': {'type': 'varchar(10)', 'choices': ['MSC', 'VSA', 'ELO', 'EXP', 'HCD', 'DIN', 'OTHER']},
            'notes': {'type': 'text', 'nullable': True},
            'owner_id': {'type': 'integer', 'fk': 'members_member'},
            'finance_card_id': {'type': 'integer', 'fk': 'credit_cards_creditcard', 'nullable': True},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
        'sensitive_note': 'NUNCA retorne _card_number ou _security_code.',
    },

    'security_storedbankaccount': {
        'description': 'Contas bancarias armazenadas no cofre (apenas metadados)',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'name': {'type': 'varchar(200)', 'searchable': True},
            'institution_name': {'type': 'varchar(200)'},
            'account_type': {'type': 'varchar(10)', 'choices': ['CC', 'CS', 'CP', 'CI', 'OTHER']},
            '_account_number': {'type': 'text', 'sensitive': True},  # ENCRYPTED
            'agency': {'type': 'varchar(50)'},
            '_password': {'type': 'text', 'sensitive': True},  # ENCRYPTED
            '_digital_password': {'type': 'text', 'sensitive': True},  # ENCRYPTED
            'notes': {'type': 'text', 'nullable': True},
            'owner_id': {'type': 'integer', 'fk': 'members_member'},
            'finance_account_id': {'type': 'integer', 'fk': 'accounts_account', 'nullable': True},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
        'sensitive_note': 'NUNCA retorne _account_number, _password ou _digital_password.',
    },

    'security_archive': {
        'description': 'Arquivos e documentos seguros',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'title': {'type': 'varchar(200)', 'searchable': True},
            'category': {'type': 'varchar(50)', 'choices': ['personal', 'financial', 'legal', 'medical', 'tax', 'work', 'other']},
            'archive_type': {'type': 'varchar(20)', 'choices': ['text', 'pdf', 'image', 'document', 'other']},
            '_encrypted_text': {'type': 'text', 'sensitive': True},  # ENCRYPTED
            'file_name': {'type': 'varchar(255)', 'nullable': True},
            'file_size': {'type': 'bigint', 'nullable': True},
            'notes': {'type': 'text', 'nullable': True},
            'tags': {'type': 'varchar(500)', 'nullable': True, 'searchable': True},
            'owner_id': {'type': 'integer', 'fk': 'members_member'},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
        'sensitive_note': 'NUNCA retorne _encrypted_text ou encrypted_file.',
    },

    # ========================================================================
    # PERSONAL PLANNING MODULE
    # ========================================================================
    'personal_planning_routinetask': {
        'description': 'Tarefas de rotina e habitos',
        'description_en': 'Routine tasks and habits',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'name': {'type': 'varchar(200)', 'searchable': True, 'description': 'Nome da tarefa'},
            'description': {'type': 'text', 'nullable': True},
            'category': {'type': 'varchar(50)', 'choices': ['health', 'studies', 'spiritual', 'exercise', 'nutrition', 'meditation', 'reading', 'writing', 'work', 'leisure', 'family', 'social', 'finance', 'household', 'personal_care', 'other']},
            'periodicity': {'type': 'varchar(20)', 'choices': ['daily', 'weekdays', 'weekly', 'monthly', 'custom']},
            'weekday': {'type': 'integer', 'nullable': True, 'description': '0=Segunda, 6=Domingo'},
            'day_of_month': {'type': 'integer', 'nullable': True},
            'custom_weekdays': {'type': 'jsonb', 'nullable': True},
            'custom_month_days': {'type': 'jsonb', 'nullable': True},
            'times_per_week': {'type': 'integer', 'nullable': True},
            'times_per_month': {'type': 'integer', 'nullable': True},
            'interval_days': {'type': 'integer', 'nullable': True},
            'interval_start_date': {'type': 'date', 'nullable': True},
            'is_active': {'type': 'boolean', 'description': 'Se esta ativa'},
            'target_quantity': {'type': 'integer', 'description': 'Meta de quantidade'},
            'unit': {'type': 'varchar(50)', 'description': 'Unidade (copos, minutos, paginas, etc.)'},
            'default_time': {'type': 'time', 'nullable': True},
            'daily_occurrences': {'type': 'integer'},
            'interval_hours': {'type': 'integer', 'nullable': True},
            'scheduled_times': {'type': 'jsonb', 'nullable': True},
            'owner_id': {'type': 'integer', 'fk': 'members_member'},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
        'common_queries': [
            'minhas tarefas de rotina',
            'habitos ativos',
            'tarefas diarias',
        ],
    },

    'personal_planning_goal': {
        'description': 'Metas pessoais',
        'description_en': 'Personal goals',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'title': {'type': 'varchar(200)', 'searchable': True, 'description': 'Titulo da meta'},
            'description': {'type': 'text', 'nullable': True},
            'goal_type': {'type': 'varchar(30)', 'choices': ['consecutive_days', 'total_days', 'avoid_habit', 'custom']},
            'related_task_id': {'type': 'integer', 'fk': 'personal_planning_routinetask', 'nullable': True},
            'target_value': {'type': 'integer', 'aggregable': True, 'description': 'Valor alvo'},
            'current_value': {'type': 'integer', 'aggregable': True, 'description': 'Valor atual'},
            'start_date': {'type': 'date'},
            'end_date': {'type': 'date', 'nullable': True},
            'status': {'type': 'varchar(20)', 'choices': GOAL_STATUSES, 'description': 'Status da meta'},
            'owner_id': {'type': 'integer', 'fk': 'members_member'},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
        'common_queries': [
            'minhas metas',
            'metas ativas',
            'progresso das metas',
        ],
    },

    'personal_planning_taskinstance': {
        'description': 'Instancias de tarefas agendadas',
        'description_en': 'Scheduled task instances',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'template_id': {'type': 'integer', 'fk': 'personal_planning_routinetask', 'nullable': True},
            'task_name': {'type': 'varchar(200)', 'searchable': True},
            'task_description': {'type': 'text', 'nullable': True},
            'category': {'type': 'varchar(50)'},
            'scheduled_date': {'type': 'date', 'description': 'Data agendada'},
            'scheduled_time': {'type': 'time', 'nullable': True},
            'occurrence_index': {'type': 'integer'},
            'status': {'type': 'varchar(20)', 'choices': TASK_STATUSES, 'description': 'Status da instancia'},
            'target_quantity': {'type': 'integer'},
            'quantity_completed': {'type': 'integer', 'aggregable': True},
            'unit': {'type': 'varchar(50)'},
            'notes': {'type': 'text', 'nullable': True},
            'started_at': {'type': 'datetime', 'nullable': True},
            'completed_at': {'type': 'datetime', 'nullable': True},
            'owner_id': {'type': 'integer', 'fk': 'members_member'},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
        'common_queries': [
            'tarefas de hoje',
            'tarefas pendentes',
            'tarefas completadas',
        ],
    },

    'personal_planning_dailyreflection': {
        'description': 'Reflexoes diarias e humor',
        'description_en': 'Daily reflections and mood',
        'owner_field': 'owner_id',
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'date': {'type': 'date', 'description': 'Data da reflexao'},
            'reflection': {'type': 'text', 'searchable': True, 'description': 'Texto da reflexao'},
            'mood': {'type': 'varchar(20)', 'choices': MOOD_CHOICES, 'description': 'Humor do dia'},
            'owner_id': {'type': 'integer', 'fk': 'members_member'},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
    },

    # ========================================================================
    # MEMBERS MODULE
    # ========================================================================
    'members_member': {
        'description': 'Membros/usuarios do sistema',
        'description_en': 'System members/users',
        'owner_field': None,  # Self-referential
        'soft_delete': True,
        'columns': {
            'id': {'type': 'integer', 'pk': True},
            'uuid': {'type': 'uuid'},
            'name': {'type': 'varchar(200)', 'searchable': True, 'description': 'Nome do membro'},
            'document': {'type': 'varchar(200)', 'description': 'CPF/documento'},
            'phone': {'type': 'varchar(200)'},
            'email': {'type': 'varchar(200)', 'nullable': True},
            'sex': {'type': 'varchar(1)', 'choices': ['M', 'F']},
            'user_id': {'type': 'integer', 'fk': 'auth_user', 'nullable': True},
            'is_creditor': {'type': 'boolean'},
            'is_benefited': {'type': 'boolean'},
            'active': {'type': 'boolean'},
            'birth_date': {'type': 'date', 'nullable': True},
            'address': {'type': 'text', 'nullable': True},
            'emergency_contact': {'type': 'varchar(200)', 'nullable': True},
            'monthly_income': {'type': 'decimal(15,2)', 'nullable': True, 'aggregable': True},
            'occupation': {'type': 'varchar(200)', 'nullable': True},
            'notes': {'type': 'text', 'nullable': True},
            'created_at': {'type': 'datetime'},
            'deleted_at': {'type': 'datetime', 'nullable': True},
            'is_deleted': {'type': 'boolean'},
        },
    },
}


# ============================================================================
# SENSITIVE FIELDS - These should NEVER be returned in SQL results
# ============================================================================

SENSITIVE_FIELDS = [
    '_password',
    '_card_number',
    '_security_code',
    '_account_number',
    '_digital_password',
    '_encrypted_text',
    'encrypted_file',
]


# ============================================================================
# TABLE ALIASES - For natural language understanding
# ============================================================================

TABLE_ALIASES = {
    # Portuguese aliases
    'livros': 'library_book',
    'livro': 'library_book',
    'books': 'library_book',
    'autores': 'library_author',
    'autor': 'library_author',
    'editoras': 'library_publisher',
    'editora': 'library_publisher',
    'leituras': 'library_reading',
    'leitura': 'library_reading',
    'resumos': 'library_summary',
    'resumo': 'library_summary',

    'despesas': 'expenses_expense',
    'despesa': 'expenses_expense',
    'gastos': 'expenses_expense',
    'gasto': 'expenses_expense',
    'expenses': 'expenses_expense',
    'despesas fixas': 'expenses_fixedexpense',

    'receitas': 'revenues_revenue',
    'receita': 'revenues_revenue',
    'ganhos': 'revenues_revenue',
    'revenues': 'revenues_revenue',

    'contas': 'accounts_account',
    'conta': 'accounts_account',
    'accounts': 'accounts_account',
    'contas bancarias': 'accounts_account',

    'cartoes': 'credit_cards_creditcard',
    'cartao': 'credit_cards_creditcard',
    'cartao de credito': 'credit_cards_creditcard',
    'faturas': 'credit_cards_creditcardbill',
    'fatura': 'credit_cards_creditcardbill',

    'transferencias': 'transfers_transfer',
    'transferencia': 'transfers_transfer',
    'transfers': 'transfers_transfer',

    'emprestimos': 'loans_loan',
    'emprestimo': 'loans_loan',
    'loans': 'loans_loan',

    'senhas': 'security_password',
    'senha': 'security_password',
    'passwords': 'security_password',
    'arquivos': 'security_archive',
    'documentos': 'security_archive',

    'tarefas': 'personal_planning_routinetask',
    'tarefa': 'personal_planning_routinetask',
    'habitos': 'personal_planning_routinetask',
    'rotina': 'personal_planning_routinetask',
    'metas': 'personal_planning_goal',
    'meta': 'personal_planning_goal',
    'goals': 'personal_planning_goal',
    'reflexoes': 'personal_planning_dailyreflection',
    'reflexao': 'personal_planning_dailyreflection',

    'membros': 'members_member',
    'membro': 'members_member',
    'usuarios': 'members_member',
}


# ============================================================================
# SCHEMA SERVICE
# ============================================================================

class SchemaService:
    """
    Service for accessing and formatting schema information.
    """

    def __init__(self):
        self.schema = MODELS_SCHEMA
        self.sensitive_fields = SENSITIVE_FIELDS
        self.table_aliases = TABLE_ALIASES

    def get_table_schema(self, table_name: str) -> Optional[Dict]:
        """Get schema for a specific table."""
        # Check if it's an alias
        if table_name.lower() in self.table_aliases:
            table_name = self.table_aliases[table_name.lower()]

        return self.schema.get(table_name)

    def get_safe_columns(self, table_name: str) -> List[str]:
        """Get list of non-sensitive columns for a table."""
        table_schema = self.get_table_schema(table_name)
        if not table_schema:
            return []

        return [
            col_name for col_name, col_def in table_schema['columns'].items()
            if not col_def.get('sensitive', False)
        ]

    def get_owner_field(self, table_name: str) -> Optional[str]:
        """Get the owner field for a table."""
        table_schema = self.get_table_schema(table_name)
        if not table_schema:
            return None
        return table_schema.get('owner_field')

    def uses_soft_delete(self, table_name: str) -> bool:
        """Check if table uses soft delete."""
        table_schema = self.get_table_schema(table_name)
        if not table_schema:
            return False
        return table_schema.get('soft_delete', False)

    def resolve_table_name(self, alias: str) -> Optional[str]:
        """Resolve a table alias to actual table name."""
        if alias in self.schema:
            return alias
        return self.table_aliases.get(alias.lower())

    def get_aggregable_columns(self, table_name: str) -> List[str]:
        """Get columns that can be used in aggregations (SUM, AVG, etc.)."""
        table_schema = self.get_table_schema(table_name)
        if not table_schema:
            return []

        return [
            col_name for col_name, col_def in table_schema['columns'].items()
            if col_def.get('aggregable', False)
        ]

    def get_searchable_columns(self, table_name: str) -> List[str]:
        """Get columns that can be used in text search."""
        table_schema = self.get_table_schema(table_name)
        if not table_schema:
            return []

        return [
            col_name for col_name, col_def in table_schema['columns'].items()
            if col_def.get('searchable', False)
        ]

    def get_schema_for_prompt(self) -> str:
        """
        Generate a formatted schema description for LLM prompts.
        """
        lines = []
        lines.append("# DATABASE SCHEMA\n")

        for table_name, table_def in self.schema.items():
            # Skip relationship tables
            if table_name.endswith('_authors'):
                continue

            lines.append(f"\n## {table_name}")
            lines.append(f"Descricao: {table_def.get('description', 'N/A')}")

            if table_def.get('owner_field'):
                lines.append(f"Campo de owner: {table_def['owner_field']}")

            if table_def.get('soft_delete'):
                lines.append("Usa soft delete: deleted_at IS NULL para registros ativos")

            if table_def.get('sensitive_note'):
                lines.append(f"ATENCAO: {table_def['sensitive_note']}")

            lines.append("\nColunas:")
            for col_name, col_def in table_def['columns'].items():
                if col_def.get('sensitive'):
                    continue  # Don't show sensitive columns

                col_type = col_def.get('type', 'unknown')
                desc = col_def.get('description', '')
                choices = col_def.get('choices', [])

                col_line = f"  - {col_name} ({col_type})"
                if desc:
                    col_line += f": {desc}"
                if choices and len(choices) <= 10:
                    col_line += f" [opcoes: {', '.join(choices)}]"
                elif choices:
                    col_line += f" [opcoes: {', '.join(choices[:5])}...]"

                lines.append(col_line)

            if table_def.get('common_queries'):
                lines.append("\nExemplos de perguntas:")
                for q in table_def['common_queries']:
                    lines.append(f"  - {q}")

        return '\n'.join(lines)

    def get_all_tables(self) -> List[str]:
        """Get list of all table names."""
        return list(self.schema.keys())

    def is_sensitive_column(self, column_name: str) -> bool:
        """Check if a column is sensitive."""
        return column_name in self.sensitive_fields or column_name.startswith('_')
