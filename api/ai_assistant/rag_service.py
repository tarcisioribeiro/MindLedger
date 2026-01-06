"""
Unified RAG (Retrieval Augmented Generation) Service for PersonalHub.

This service provides semantic search across all modules:
- Finance: Expenses, revenues, accounts, credit cards
- Security: Passwords, stored cards, accounts, archives
- Library: Books, summaries, readings

Uses OpenAI API for embeddings and Groq API for generation.
"""

import os
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np
from openai import OpenAI
from groq import Groq


@dataclass
class SearchResult:
    """Represents a search result from any module."""
    module: str  # finance, security, library
    entity_type: str  # expense, book, password, etc.
    content: str
    metadata: Dict[str, Any]
    score: float
    entity_id: int


class UnifiedRAGService:
    """
    Unified RAG service that searches across all PersonalHub modules.
    """

    def __init__(self):
        # Initialize OpenAI client for embeddings
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key or openai_api_key == 'your_openai_api_key_here':
            self.openai_client = None
        else:
            try:
                self.openai_client = OpenAI(api_key=openai_api_key)
            except Exception as e:
                print(f"[RAG] Erro ao inicializar OpenAI client: {e}")
                self.openai_client = None

        # Initialize Groq client for text generation
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key or groq_api_key == 'your_groq_api_key_here':
            self.groq_client = None
        else:
            try:
                self.groq_client = Groq(api_key=groq_api_key)
            except Exception as e:
                print(f"[RAG] Erro ao inicializar Groq client: {e}")
                self.groq_client = None

    def _get_library_content(self, user_member) -> List[Dict[str, Any]]:
        """Get searchable content from Library module."""
        from library.models import Book, Summary, Reading

        content = []

        # Books
        books = Book.objects.filter(owner=user_member, deleted_at__isnull=True)
        for book in books:
            authors = ', '.join(book.authors_names) if hasattr(book, 'authors_names') else ''
            content.append({
                'module': 'library',
                'entity_type': 'book',
                'text': f"Livro: {book.title}. Autores: {authors}. Sinopse: {book.synopsis}. Gênero: {book.get_genre_display()}. Tipo: {book.get_literarytype_display()}.",
                'metadata': {
                    'id': book.id,
                    'title': book.title,
                    'authors': authors,
                    'pages': book.pages,
                    'read_status': book.get_read_status_display(),
                    'rating': book.rating
                }
            })

        # Summaries
        summaries = Summary.objects.filter(owner=user_member, deleted_at__isnull=True)
        for summary in summaries:
            content.append({
                'module': 'library',
                'entity_type': 'summary',
                'text': f"Resumo do livro {summary.book.title}: {summary.content[:500]}...",
                'metadata': {
                    'id': summary.id,
                    'book_title': summary.book.title,
                    'is_vectorized': summary.is_vectorized
                }
            })

        return content

    def _get_finance_content(self, user_member) -> List[Dict[str, Any]]:
        """Get searchable content from Finance module."""
        from expenses.models import Expense
        from revenues.models import Revenue
        from accounts.models import Account
        from credit_cards.models import CreditCard, CreditCardBill, CreditCardExpense
        from transfers.models import Transfer
        from loans.models import Loan

        content = []

        # Expenses
        expenses = Expense.objects.filter(member=user_member, deleted_at__isnull=True)[:100]  # Limit for performance
        for expense in expenses:
            content.append({
                'module': 'finance',
                'entity_type': 'expense',
                'text': f"Despesa: {expense.description}. Categoria: {expense.get_category_display()}. Valor: R$ {expense.value}. Data: {expense.date}. Estabelecimento: {expense.merchant or 'N/A'}. Observações: {expense.notes or 'N/A'}.",
                'metadata': {
                    'id': expense.id,
                    'description': expense.description,
                    'value': float(expense.value),
                    'category': expense.get_category_display(),
                    'date': str(expense.date),
                    'merchant': expense.merchant
                }
            })

        # Revenues
        revenues = Revenue.objects.filter(member=user_member, deleted_at__isnull=True)[:100]
        for revenue in revenues:
            content.append({
                'module': 'finance',
                'entity_type': 'revenue',
                'text': f"Receita: {revenue.description}. Categoria: {revenue.get_category_display()}. Valor: R$ {revenue.value}. Data: {revenue.date}. Fonte: {revenue.source or 'N/A'}. Observações: {revenue.notes or 'N/A'}.",
                'metadata': {
                    'id': revenue.id,
                    'description': revenue.description,
                    'value': float(revenue.value),
                    'category': revenue.get_category_display(),
                    'date': str(revenue.date),
                    'source': revenue.source
                }
            })

        # Accounts
        accounts = Account.objects.filter(owner=user_member, deleted_at__isnull=True)
        for account in accounts:
            content.append({
                'module': 'finance',
                'entity_type': 'account',
                'text': f"Conta: {account.account_name}. Tipo: {account.get_account_type_display()}. Instituição: {account.get_institution_name_display()}. Saldo Atual: R$ {account.current_balance}. Descrição: {account.description or 'N/A'}.",
                'metadata': {
                    'id': account.id,
                    'name': account.account_name,
                    'balance': float(account.current_balance),
                    'account_type': account.get_account_type_display(),
                    'institution': account.get_institution_name_display()
                }
            })

        # Credit Cards
        credit_cards = CreditCard.objects.filter(owner=user_member, deleted_at__isnull=True)
        for card in credit_cards:
            content.append({
                'module': 'finance',
                'entity_type': 'credit_card',
                'text': f"Cartão de Crédito: {card.name}. Bandeira: {card.get_flag_display()}. Limite: R$ {card.credit_limit}. Limite Disponível: R$ {card.max_limit}. Observações: {card.notes or 'N/A'}.",
                'metadata': {
                    'id': card.id,
                    'name': card.name,
                    'flag': card.get_flag_display(),
                    'credit_limit': float(card.credit_limit),
                    'is_active': card.is_active
                }
            })

        # Credit Card Expenses
        cc_expenses = CreditCardExpense.objects.filter(member=user_member, deleted_at__isnull=True)[:100]
        for expense in cc_expenses:
            content.append({
                'module': 'finance',
                'entity_type': 'credit_card_expense',
                'text': f"Despesa de Cartão: {expense.description}. Valor: R$ {expense.value}. Data: {expense.date}. Parcela: {expense.installment}/{expense.total_installments}. Estabelecimento: {expense.merchant or 'N/A'}.",
                'metadata': {
                    'id': expense.id,
                    'description': expense.description,
                    'value': float(expense.value),
                    'date': str(expense.date),
                    'installments': f"{expense.installment}/{expense.total_installments}"
                }
            })

        # Transfers
        transfers = Transfer.objects.filter(member=user_member, deleted_at__isnull=True)[:100]
        for transfer in transfers:
            content.append({
                'module': 'finance',
                'entity_type': 'transfer',
                'text': f"Transferência: {transfer.description}. Valor: R$ {transfer.value}. Data: {transfer.date}. Tipo: {transfer.get_category_display()}. Observações: {transfer.notes or 'N/A'}.",
                'metadata': {
                    'id': transfer.id,
                    'description': transfer.description,
                    'value': float(transfer.value),
                    'date': str(transfer.date),
                    'category': transfer.get_category_display()
                }
            })

        # Loans
        loans = Loan.objects.filter(deleted_at__isnull=True)[:100]
        # Filter by creditor or benefited
        user_loans = [loan for loan in loans if loan.creditor == user_member or loan.benefited == user_member]
        for loan in user_loans:
            content.append({
                'module': 'finance',
                'entity_type': 'loan',
                'text': f"Empréstimo: {loan.description}. Valor Total: R$ {loan.value}. Valor Pago: R$ {loan.payed_value}. Data: {loan.date}. Status: {loan.get_status_display()}. Categoria: {loan.get_category_display()}. Observações: {loan.notes or 'N/A'}.",
                'metadata': {
                    'id': loan.id,
                    'description': loan.description,
                    'value': float(loan.value),
                    'payed_value': float(loan.payed_value),
                    'date': str(loan.date),
                    'status': loan.get_status_display()
                }
            })

        return content

    def _get_security_content(self, user_member) -> List[Dict[str, Any]]:
        """Get searchable content from Security module."""
        from passwords.models import Password
        from archives.models import Archive

        content = []

        # Passwords (excluding sensitive data)
        passwords = Password.objects.filter(owner=user_member, deleted_at__isnull=True)
        for password in passwords:
            content.append({
                'module': 'security',
                'entity_type': 'password',
                'text': f"Senha: {password.name}. Website: {password.website or 'N/A'}. Usuário: {password.username or 'N/A'}. Observações: {password.notes or 'N/A'}.",
                'metadata': {
                    'id': password.id,
                    'name': password.name,
                    'website': password.website
                }
            })

        # Archives
        archives = Archive.objects.filter(owner=user_member, deleted_at__isnull=True)
        for archive in archives:
            content.append({
                'module': 'security',
                'entity_type': 'archive',
                'text': f"Arquivo: {archive.name}. Descrição: {archive.description or 'N/A'}.",
                'metadata': {
                    'id': archive.id,
                    'name': archive.name
                }
            })

        return content

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using OpenAI API.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not self.openai_client:
            raise ValueError("OpenAI API não configurada. Por favor, configure OPENAI_API_KEY no arquivo .env com uma chave válida da OpenAI (https://platform.openai.com/api-keys)")

        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise Exception(f"Erro ao gerar embeddings: {str(e)}")

    def search(self, query: str, user_member, top_k: int = 5) -> List[SearchResult]:
        """
        Perform semantic search across all modules.

        Args:
            query: User's search query
            user_member: Member object for filtering data
            top_k: Number of top results to return

        Returns:
            List of SearchResult objects ranked by relevance
        """
        # Get content from all modules
        all_content = []
        all_content.extend(self._get_library_content(user_member))
        all_content.extend(self._get_finance_content(user_member))
        all_content.extend(self._get_security_content(user_member))

        if not all_content:
            return []

        # Generate embeddings using OpenAI API
        doc_texts = [item['text'] for item in all_content]
        all_texts = [query] + doc_texts
        all_embeddings = self._get_embeddings(all_texts)

        query_embedding = np.array(all_embeddings[0])
        doc_embeddings = np.array(all_embeddings[1:])

        # Calculate cosine similarity
        scores = np.dot(doc_embeddings, query_embedding) / (
            np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Get top-k results
        top_indices = np.argsort(scores)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            item = all_content[idx]
            results.append(SearchResult(
                module=item['module'],
                entity_type=item['entity_type'],
                content=item['text'],
                metadata=item['metadata'],
                score=float(scores[idx]),
                entity_id=item['metadata']['id']
            ))

        return results

    def generate_answer(self, query: str, context_results: List[SearchResult]) -> str:
        """
        Generate an answer using Groq API based on retrieved context.

        Args:
            query: User's question
            context_results: Retrieved search results

        Returns:
            Generated answer
        """
        if not self.groq_client:
            raise ValueError("API Groq não configurada. Por favor, configure GROQ_API_KEY no arquivo .env com uma chave válida da Groq (https://console.groq.com/keys)")

        # Build context from search results
        context = "\n\n".join([
            f"[{r.module.upper()} - {r.entity_type}]\n{r.content}"
            for r in context_results
        ])

        # Create prompt
        system_prompt = """Você é um assistente inteligente do PersonalHub, uma plataforma unificada de gestão pessoal.
Você tem acesso a informações de três módulos:
- Finance: Despesas, receitas, contas bancárias e cartões de crédito
- Security: Senhas, cartões armazenados, contas bancárias e arquivos seguros
- Library: Livros, resumos e registros de leitura

Baseie suas respostas APENAS nas informações fornecidas no contexto.
Se a informação não estiver no contexto, diga que não encontrou.
Seja conciso, objetivo e útil."""

        user_prompt = f"""Contexto relevante:
{context}

Pergunta do usuário: {query}

Responda a pergunta baseando-se APENAS no contexto fornecido acima."""

        try:
            # Call Groq API
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile",  # Fast and capable model
                temperature=0.3,
                max_tokens=500
            )

            return chat_completion.choices[0].message.content

        except Exception as e:
            return f"Erro ao gerar resposta: {str(e)}"

    def query(self, question: str, user_member, top_k: int = 5) -> Dict[str, Any]:
        """
        Complete RAG pipeline: search + generate answer.

        Args:
            question: User's question
            user_member: Member object for filtering data
            top_k: Number of context results to use

        Returns:
            Dict with answer and sources
        """
        # Search for relevant content
        results = self.search(question, user_member, top_k=top_k)

        if not results:
            return {
                'answer': 'Não encontrei informações relevantes nos seus dados.',
                'sources': []
            }

        # Generate answer
        answer = self.generate_answer(question, results)

        # Format sources
        sources = [
            {
                'module': r.module,
                'type': r.entity_type,
                'score': round(r.score, 3),
                'metadata': r.metadata
            }
            for r in results
        ]

        return {
            'answer': answer,
            'sources': sources
        }


# Singleton instance
_rag_service = None

def get_rag_service() -> UnifiedRAGService:
    """Get singleton instance of RAG service."""
    global _rag_service
    if _rag_service is None:
        _rag_service = UnifiedRAGService()
    return _rag_service
