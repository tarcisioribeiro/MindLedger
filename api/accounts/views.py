from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from accounts.models import Account
from accounts.serializers import AccountSerializer
from app.permissions import GlobalDefaultPermission


class AccountCreateListView(generics.ListCreateAPIView):
    """
    ViewSet para listar e criar contas bancárias.

    Permite:
    - GET: Lista todas as contas ordenadas por nome (exclui deletadas)
    - POST: Cria uma nova conta

    Attributes
    ----------
    permission_classes : tuple
        Permissões necessárias (IsAuthenticated, GlobalDefaultPermission)
    queryset : QuerySet
        QuerySet de contas não deletadas
    serializer_class : class
        Serializer usado para validação e serialização
    ordering : list
        Ordenação padrão por nome
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    serializer_class = AccountSerializer
    ordering = ['name']  # Consistent ordering

    def get_queryset(self):
        # Usa defer() para excluir campo criptografado na listagem (performance)
        return Account.objects.filter(is_deleted=False).defer('_account_number')


class AccountRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    ViewSet para operações individuais em contas bancárias.

    Permite:
    - GET: Recupera uma conta específica (exclui deletadas)
    - PUT/PATCH: Atualiza uma conta existente
    - DELETE: Remove uma conta (soft delete)

    Attributes
    ----------
    permission_classes : tuple
        Permissões necessárias (IsAuthenticated, GlobalDefaultPermission)
    queryset : QuerySet
        QuerySet de contas não deletadas
    serializer_class : class
        Serializer usado para validação e serialização
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = Account.objects.filter(is_deleted=False)
    serializer_class = AccountSerializer
