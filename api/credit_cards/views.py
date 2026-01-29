from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from credit_cards.models import (
    CreditCard,
    CreditCardBill,
    CreditCardExpense,
    CreditCardPurchase,
    CreditCardInstallment,
)
from credit_cards.serializers import (
    CreditCardSerializer,
    CreditCardBillsSerializer,
    CreditCardExpensesSerializer,
    CreditCardPurchaseSerializer,
    CreditCardPurchaseCreateSerializer,
    CreditCardPurchaseUpdateSerializer,
    CreditCardInstallmentSerializer,
    CreditCardInstallmentUpdateSerializer,
    PayCreditCardBillSerializer,
)
from expenses.models import Expense
from app.permissions import GlobalDefaultPermission


class CreditCardCreateListView(generics.ListCreateAPIView):
    """
    ViewSet para listar e criar cartões de crédito.

    Permite:
    - GET: Lista todos os cartões de crédito com conta associada
    - POST: Cria um novo cartão de crédito

    Attributes
    ----------
    permission_classes : tuple
        Permissões necessárias (IsAuthenticated, GlobalDefaultPermission)
    queryset : QuerySet
        QuerySet dos cartões (exclui deletados) com conta associada carregada
    serializer_class : class
        Serializer usado para validação e serialização
    ordering : list
        Ordenação padrão por nome
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    serializer_class = CreditCardSerializer
    ordering = ['name']

    def get_queryset(self):
        # Usa defer() para excluir campo criptografado na listagem (performance)
        return CreditCard.objects.filter(
            is_deleted=False
        ).select_related(
            'associated_account'
        ).defer('_card_number')


class CreditCardRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    """
    ViewSet para operações individuais em cartões de crédito.

    Permite:
    - GET: Recupera um cartão específico
    - PUT/PATCH: Atualiza um cartão existente
    - DELETE: Remove um cartão

    Attributes
    ----------
    permission_classes : tuple
        Permissões necessárias (IsAuthenticated, GlobalDefaultPermission)
    queryset : QuerySet
        QuerySet dos cartões (exclui deletados) com conta associada carregada
    serializer_class : class
        Serializer usado para validação e serialização
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = CreditCard.objects.filter(is_deleted=False).select_related('associated_account')
    serializer_class = CreditCardSerializer


class CreditCardBillCreateListView(generics.ListCreateAPIView):
    """
    ViewSet para listar e criar faturas de cartão de crédito.

    Permite:
    - GET: Lista todas as faturas ordenadas por data
    - POST: Cria uma nova fatura

    Attributes
    ----------
    permission_classes : tuple
        Permissões necessárias (IsAuthenticated, GlobalDefaultPermission)
    queryset : QuerySet
        QuerySet das faturas (exclui deletadas) com cartão e conta associada carregados
    serializer_class : class
        Serializer usado para validação e serialização
    ordering : list
        Ordenação por ano, mês e data de fim da fatura (descendente)
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = CreditCardBill.objects.filter(is_deleted=False).select_related(
        'credit_card',
        'credit_card__associated_account'
    )
    serializer_class = CreditCardBillsSerializer
    ordering = ['-year', '-month', '-invoice_ending_date']


class CreditCardBillRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    """
    ViewSet para operações individuais em faturas de cartão.

    Permite:
    - GET: Recupera uma fatura específica
    - PUT/PATCH: Atualiza uma fatura existente
    - DELETE: Remove uma fatura

    Attributes
    ----------
    permission_classes : tuple
        Permissões necessárias (IsAuthenticated, GlobalDefaultPermission)
    queryset : QuerySet
        QuerySet das faturas (exclui deletadas) com cartão e conta associada carregados
    serializer_class : class
        Serializer usado para validação e serialização
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = CreditCardBill.objects.filter(is_deleted=False).select_related(
        'credit_card', 'credit_card__associated_account'
    )
    serializer_class = CreditCardBillsSerializer


class CreditCardExpenseCreateListView(generics.ListCreateAPIView):
    """
    ViewSet para listar e criar despesas de cartão de crédito.

    Permite:
    - GET: Lista todas as despesas do cartão ordenadas por data
    - POST: Cria uma nova despesa no cartão

    Attributes
    ----------
    permission_classes : tuple
        Permissões necessárias (IsAuthenticated, GlobalDefaultPermission)
    queryset : QuerySet
        QuerySet das despesas (exclui deletadas) com cartão e conta associada carregados
    serializer_class : class
        Serializer usado para validação e serialização
    ordering : list
        Ordenação por data e ID (descendente)
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = CreditCardExpense.objects.filter(is_deleted=False).select_related(
        'card', 'card__associated_account'
    )
    serializer_class = CreditCardExpensesSerializer
    ordering = ['-date', '-id']


class CreditCardExpenseRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    """
    ViewSet para operações individuais em despesas de cartão.

    Permite:
    - GET: Recupera uma despesa específica
    - PUT/PATCH: Atualiza uma despesa existente
    - DELETE: Remove uma despesa

    Attributes
    ----------
    permission_classes : tuple
        Permissões necessárias (IsAuthenticated, GlobalDefaultPermission)
    queryset : QuerySet
        QuerySet das despesas (exclui deletadas) com cartão e conta associada carregados
    serializer_class : class
        Serializer usado para validação e serialização
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = CreditCardExpense.objects.filter(is_deleted=False).select_related(
        'card', 'card__associated_account'
    )
    serializer_class = CreditCardExpensesSerializer


# ============================================================================
# NEW VIEWS FOR PURCHASE AND INSTALLMENT
# ============================================================================

class CreditCardPurchaseCreateListView(generics.ListCreateAPIView):
    """
    ViewSet para listar e criar compras de cartão de crédito.

    Permite:
    - GET: Lista todas as compras com parcelas aninhadas
    - POST: Cria uma nova compra (parcelas são geradas automaticamente)

    Query params para filtro:
    - card: ID do cartão
    - category: Categoria da compra
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = CreditCardPurchase.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['card', 'category']
    ordering = ['-purchase_date', '-id']

    def get_queryset(self):
        return CreditCardPurchase.objects.filter(is_deleted=False).select_related(
            'card', 'card__associated_account', 'member'
        ).prefetch_related(
            'installments', 'installments__bill'
        )

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreditCardPurchaseCreateSerializer
        return CreditCardPurchaseSerializer


class CreditCardPurchaseRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    """
    ViewSet para operações individuais em compras de cartão.

    Permite:
    - GET: Recupera uma compra específica com parcelas
    - PUT/PATCH: Atualiza uma compra existente (exceto valor e parcelas)
    - DELETE: Remove uma compra e suas parcelas

    Attributes
    ----------
    permission_classes : tuple
        Permissões necessárias (IsAuthenticated, GlobalDefaultPermission)
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = CreditCardPurchase.objects.all()

    def get_queryset(self):
        return CreditCardPurchase.objects.filter(is_deleted=False).select_related(
            'card', 'card__associated_account', 'member'
        ).prefetch_related(
            'installments', 'installments__bill'
        )

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CreditCardPurchaseUpdateSerializer
        return CreditCardPurchaseSerializer


class CreditCardInstallmentListView(generics.ListAPIView):
    """
    ViewSet para listar parcelas de cartão de crédito.

    Query params para filtro:
    - card: ID do cartão (via purchase__card)
    - bill: ID da fatura
    - category: Categoria (via purchase__category)
    - payed: Status de pagamento (true/false)
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = CreditCardInstallment.objects.all()
    serializer_class = CreditCardInstallmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'purchase__card': ['exact'],
        'bill': ['exact', 'isnull'],
        'purchase__category': ['exact'],
        'payed': ['exact'],
    }
    ordering = ['due_date', 'purchase__description']

    def get_queryset(self):
        return CreditCardInstallment.objects.filter(
            is_deleted=False,
            purchase__is_deleted=False
        ).select_related(
            'purchase', 'purchase__card', 'purchase__member', 'bill'
        )


class CreditCardInstallmentUpdateView(generics.UpdateAPIView):
    """
    ViewSet para atualizar uma parcela específica.

    Permite alterar apenas:
    - bill: Fatura associada
    - payed: Status de pagamento
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = CreditCardInstallment.objects.all()
    serializer_class = CreditCardInstallmentUpdateSerializer

    def get_queryset(self):
        return CreditCardInstallment.objects.filter(
            is_deleted=False,
            purchase__is_deleted=False
        ).select_related('purchase', 'bill')


class PayCreditCardBillView(APIView):
    """
    View para pagar uma fatura de cartão de crédito.

    POST /api/v1/credit-cards-bills/{id}/pay/

    Lógica:
    1. Busca a fatura e o cartão associado
    2. Valida os dados do pagamento
    3. Cria uma despesa na conta associada ao cartão (payed=True)
    4. Atualiza o paid_amount da fatura
    5. Atualiza o credit_limit do cartão
    6. Atualiza o status da fatura conforme regras de negócio
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    # Required for GlobalDefaultPermission to derive model permissions
    queryset = CreditCardBill.objects.all()

    @transaction.atomic
    def post(self, request, pk):
        # 1. Buscar a fatura
        try:
            bill = CreditCardBill.objects.select_related(
                'credit_card',
                'credit_card__associated_account'
            ).get(pk=pk, is_deleted=False)
        except CreditCardBill.DoesNotExist:
            return Response(
                {'detail': 'Fatura não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        card = bill.credit_card
        account = card.associated_account

        # 2. Validar os dados do pagamento
        serializer = PayCreditCardBillSerializer(
            data=request.data,
            context={'bill': bill}
        )
        serializer.is_valid(raise_exception=True)

        amount = Decimal(str(serializer.validated_data['amount']))
        payment_date = serializer.validated_data['payment_date']
        notes = serializer.validated_data.get('notes', '')

        # Verificar se a fatura já está paga
        remaining = Decimal(str(bill.total_amount)) - Decimal(str(bill.paid_amount))
        if remaining <= 0:
            return Response(
                {'detail': 'Esta fatura já foi totalmente paga'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Criar despesa na conta associada
        expense_description = f"Pagamento fatura {card.name} - {bill.month}/{bill.year}"
        if notes:
            expense_description += f" ({notes})"

        expense = Expense.objects.create(
            description=expense_description,
            value=amount,
            date=payment_date,
            horary=timezone.now().time(),
            category='bills and services',
            account=account,
            payed=True,
            merchant=card.name,
            payment_method='transfer',
            notes=notes or f"Pagamento de fatura do cartão {card.name}",
            related_bill_payment=bill,
        )

        # 4. Atualizar paid_amount da fatura
        bill.paid_amount = Decimal(str(bill.paid_amount)) + amount
        bill.payment_date = payment_date

        # 5. Atualizar status da fatura conforme regras de negócio
        new_paid_amount = Decimal(str(bill.paid_amount))
        total_amount = Decimal(str(bill.total_amount))

        if new_paid_amount >= total_amount:
            # Fatura totalmente paga
            bill.status = 'paid'
            bill.closed = True

            # 5.1 Marcar todas as parcelas desta fatura como pagas
            # Isso libera o limite do cartão automaticamente no cálculo
            CreditCardInstallment.objects.filter(
                bill=bill,
                is_deleted=False,
                payed=False
            ).update(payed=True)

        elif bill.due_date and payment_date >= bill.due_date:
            # Pagamento parcial após o vencimento
            if bill.status != 'overdue':
                bill.status = 'closed'
            bill.closed = True
        # Se pagamento parcial antes do vencimento, mantém status atual

        bill.save()

        # Retornar dados atualizados
        return Response({
            'message': 'Pagamento realizado com sucesso',
            'payment': {
                'amount': str(amount),
                'payment_date': str(payment_date),
                'expense_id': expense.id,
            },
            'bill': {
                'id': bill.id,
                'total_amount': str(bill.total_amount),
                'paid_amount': str(bill.paid_amount),
                'remaining': str(total_amount - new_paid_amount),
                'status': bill.status,
                'closed': bill.closed,
            },
            'card': {
                'id': card.id,
                'name': card.name,
                'credit_limit': str(card.credit_limit),
                'max_limit': str(card.max_limit),
            },
            'account': {
                'id': account.id,
                'name': account.account_name,
                'balance': str(account.current_balance),
            }
        }, status=status.HTTP_200_OK)
