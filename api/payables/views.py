from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from payables.models import Payable
from payables.serializers import PayableSerializer
from app.permissions import GlobalDefaultPermission


class PayableCreateListView(generics.ListCreateAPIView):
    """
    ViewSet para listar e criar Payables (valores a pagar).

    Permite:
    - GET: Lista todos os payables (exclui deletados)
    - POST: Cria um novo payable

    Attributes
    ----------
    permission_classes : tuple
        Permissões necessárias (IsAuthenticated, GlobalDefaultPermission)
    queryset : QuerySet
        QuerySet de payables não deletados
    serializer_class : class
        Serializer usado para validação e serialização
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = Payable.objects.filter(is_deleted=False)
    serializer_class = PayableSerializer


class PayableRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    ViewSet para operações individuais em Payables.

    Permite:
    - GET: Recupera um payable específico (exclui deletados)
    - PUT/PATCH: Atualiza um payable existente
    - DELETE: Remove um payable (soft delete)

    Attributes
    ----------
    permission_classes : tuple
        Permissões necessárias (IsAuthenticated, GlobalDefaultPermission)
    queryset : QuerySet
        QuerySet de payables não deletados
    serializer_class : class
        Serializer usado para validação e serialização
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = Payable.objects.filter(is_deleted=False)
    serializer_class = PayableSerializer
