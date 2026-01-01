from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count
from app.permissions import GlobalDefaultPermission
from security.models import (
    Password, StoredCreditCard, StoredBankAccount,
    Archive, PASSWORD_CATEGORIES
)
from security.activity_logs.models import ActivityLog, ACTION_TYPES
from security.serializers import (
    PasswordSerializer, PasswordCreateUpdateSerializer, PasswordRevealSerializer,
    StoredCreditCardSerializer, StoredCreditCardCreateUpdateSerializer, StoredCreditCardRevealSerializer,
    StoredBankAccountSerializer, StoredBankAccountCreateUpdateSerializer, StoredBankAccountRevealSerializer,
    ArchiveSerializer, ArchiveCreateUpdateSerializer, ArchiveRevealSerializer,
    ActivityLogSerializer
)


def get_client_ip(request):
    """Extrai o IP do cliente da requisição."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(request, action, model_name, object_id, description):
    """Helper para registrar atividades."""
    ActivityLog.log_action(
        user=request.user,
        action=action,
        description=description,
        model_name=model_name,
        object_id=object_id,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )


# ============================================================================
# PASSWORD VIEWS
# ============================================================================

class PasswordListCreateView(generics.ListCreateAPIView):
    """Lista todas as senhas ou cria uma nova."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Password.objects.all()

    def get_queryset(self):
        return Password.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PasswordCreateUpdateSerializer
        return PasswordSerializer

    def perform_create(self, serializer):
        password = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            self.request,
            'create',
            'Password',
            password.id,
            f'Criou senha: {password.title}'
        )


class PasswordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, atualiza ou deleta uma senha."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Password.objects.all()

    def get_queryset(self):
        return Password.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PasswordCreateUpdateSerializer
        return PasswordSerializer

    def perform_update(self, serializer):
        password = serializer.save(updated_by=self.request.user)
        log_activity(
            self.request,
            'update',
            'Password',
            password.id,
            f'Atualizou senha: {password.title}'
        )

    def perform_destroy(self, instance):
        # Soft delete
        instance.deleted_at = instance.updated_at
        instance.deleted_by = self.request.user
        instance.save()
        log_activity(
            self.request,
            'delete',
            'Password',
            instance.id,
            f'Deletou senha: {instance.title}'
        )


class PasswordRevealView(generics.RetrieveAPIView):
    """Revela a senha descriptografada (com log de auditoria)."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    serializer_class = PasswordRevealSerializer
    queryset = Password.objects.all()

    def get_queryset(self):
        return Password.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Log da revelação
        log_activity(
            request,
            'reveal',
            'Password',
            instance.id,
            f'Revelou senha: {instance.title}'
        )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# ============================================================================
# STORED CREDIT CARD VIEWS
# ============================================================================

class StoredCreditCardListCreateView(generics.ListCreateAPIView):
    """Lista todos os cartões ou cria um novo."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = StoredCreditCard.objects.all()

    def get_queryset(self):
        return StoredCreditCard.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'finance_card')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StoredCreditCardCreateUpdateSerializer
        return StoredCreditCardSerializer

    def perform_create(self, serializer):
        card = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            self.request,
            'create',
            'StoredCreditCard',
            card.id,
            f'Criou cartão: {card.name}'
        )


class StoredCreditCardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, atualiza ou deleta um cartão."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = StoredCreditCard.objects.all()

    def get_queryset(self):
        return StoredCreditCard.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'finance_card')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return StoredCreditCardCreateUpdateSerializer
        return StoredCreditCardSerializer

    def perform_update(self, serializer):
        card = serializer.save(updated_by=self.request.user)
        log_activity(
            self.request,
            'update',
            'StoredCreditCard',
            card.id,
            f'Atualizou cartão: {card.name}'
        )

    def perform_destroy(self, instance):
        instance.deleted_at = instance.updated_at
        instance.deleted_by = self.request.user
        instance.save()
        log_activity(
            self.request,
            'delete',
            'StoredCreditCard',
            instance.id,
            f'Deletou cartão: {instance.name}'
        )


class StoredCreditCardRevealView(generics.RetrieveAPIView):
    """Revela dados completos do cartão (com log de auditoria)."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    serializer_class = StoredCreditCardRevealSerializer
    queryset = StoredCreditCard.objects.all()

    def get_queryset(self):
        return StoredCreditCard.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        log_activity(
            request,
            'reveal',
            'StoredCreditCard',
            instance.id,
            f'Revelou dados do cartão: {instance.name}'
        )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# ============================================================================
# STORED BANK ACCOUNT VIEWS
# ============================================================================

class StoredBankAccountListCreateView(generics.ListCreateAPIView):
    """Lista todas as contas bancárias ou cria uma nova."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = StoredBankAccount.objects.all()

    def get_queryset(self):
        return StoredBankAccount.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'finance_account')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StoredBankAccountCreateUpdateSerializer
        return StoredBankAccountSerializer

    def perform_create(self, serializer):
        account = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            self.request,
            'create',
            'StoredBankAccount',
            account.id,
            f'Criou conta bancária: {account.name}'
        )


class StoredBankAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, atualiza ou deleta uma conta bancária."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = StoredBankAccount.objects.all()

    def get_queryset(self):
        return StoredBankAccount.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'finance_account')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return StoredBankAccountCreateUpdateSerializer
        return StoredBankAccountSerializer

    def perform_update(self, serializer):
        account = serializer.save(updated_by=self.request.user)
        log_activity(
            self.request,
            'update',
            'StoredBankAccount',
            account.id,
            f'Atualizou conta bancária: {account.name}'
        )

    def perform_destroy(self, instance):
        instance.deleted_at = instance.updated_at
        instance.deleted_by = self.request.user
        instance.save()
        log_activity(
            self.request,
            'delete',
            'StoredBankAccount',
            instance.id,
            f'Deletou conta bancária: {instance.name}'
        )


class StoredBankAccountRevealView(generics.RetrieveAPIView):
    """Revela dados completos da conta bancária (com log de auditoria)."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    serializer_class = StoredBankAccountRevealSerializer
    queryset = StoredBankAccount.objects.all()

    def get_queryset(self):
        return StoredBankAccount.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        log_activity(
            request,
            'reveal',
            'StoredBankAccount',
            instance.id,
            f'Revelou dados da conta: {instance.name}'
        )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# ============================================================================
# ARCHIVE VIEWS
# ============================================================================

class ArchiveListCreateView(generics.ListCreateAPIView):
    """Lista todos os arquivos ou cria um novo."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Archive.objects.all()

    def get_queryset(self):
        return Archive.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ArchiveCreateUpdateSerializer
        return ArchiveSerializer

    def perform_create(self, serializer):
        archive = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            self.request,
            'create',
            'Archive',
            archive.id,
            f'Criou arquivo: {archive.title}'
        )


class ArchiveDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, atualiza ou deleta um arquivo."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Archive.objects.all()

    def get_queryset(self):
        return Archive.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ArchiveCreateUpdateSerializer
        return ArchiveSerializer

    def perform_update(self, serializer):
        archive = serializer.save(updated_by=self.request.user)
        log_activity(
            self.request,
            'update',
            'Archive',
            archive.id,
            f'Atualizou arquivo: {archive.title}'
        )

    def perform_destroy(self, instance):
        instance.deleted_at = instance.updated_at
        instance.deleted_by = self.request.user
        instance.save()
        log_activity(
            self.request,
            'delete',
            'Archive',
            instance.id,
            f'Deletou arquivo: {instance.title}'
        )


class ArchiveRevealView(generics.RetrieveAPIView):
    """Revela conteúdo de texto do arquivo (com log de auditoria)."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    serializer_class = ArchiveRevealSerializer
    queryset = Archive.objects.all()

    def get_queryset(self):
        return Archive.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        log_activity(
            request,
            'reveal',
            'Archive',
            instance.id,
            f'Revelou conteúdo do arquivo: {instance.title}'
        )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# ============================================================================
# ACTIVITY LOG VIEWS
# ============================================================================

class ActivityLogListView(generics.ListAPIView):
    """Lista logs de atividades (somente leitura)."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    serializer_class = ActivityLogSerializer
    queryset = ActivityLog.objects.all()

    def get_queryset(self):
        return ActivityLog.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


# ============================================================================
# SECURITY DASHBOARD VIEWS
# ============================================================================

class SecurityDashboardStatsView(APIView):
    """
    GET /api/v1/security/dashboard/stats/

    Retorna estatísticas agregadas do módulo de Segurança.

    Response:
    {
        "total_passwords": 15,
        "total_stored_cards": 3,
        "total_stored_accounts": 2,
        "total_archives": 5,
        "passwords_by_category": [
            {"category": "social", "category_display": "Redes Sociais", "count": 5},
            {"category": "email", "category_display": "E-mail", "count": 3}
        ],
        "recent_activity": [
            {
                "action": "create",
                "action_display": "Criação",
                "model_name": "Password",
                "description": "Criou senha: Gmail",
                "created_at": "2025-03-15T10:30:00Z"
            }
        ]
    }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Calcula estatísticas do módulo de segurança."""
        user = request.user

        # Verificar se o usuário tem um member associado
        from members.models import Member
        try:
            member = Member.objects.get(user=user, is_deleted=False)
        except Member.DoesNotExist:
            # Se não houver member, retornar estatísticas vazias
            return Response({
                'total_passwords': 0,
                'total_stored_cards': 0,
                'total_stored_accounts': 0,
                'total_archives': 0,
                'passwords_by_category': [],
                'recent_activity': []
            })

        # Querysets filtrados por owner e não deletados
        passwords_qs = Password.objects.filter(
            owner=member,
            deleted_at__isnull=True
        )
        stored_cards_qs = StoredCreditCard.objects.filter(
            owner=member,
            deleted_at__isnull=True
        )
        stored_accounts_qs = StoredBankAccount.objects.filter(
            owner=member,
            deleted_at__isnull=True
        )
        archives_qs = Archive.objects.filter(
            owner=member,
            deleted_at__isnull=True
        )

        # Contadores
        total_passwords = passwords_qs.count()
        total_stored_cards = stored_cards_qs.count()
        total_stored_accounts = stored_accounts_qs.count()
        total_archives = archives_qs.count()

        # Senhas por categoria (Top 5)
        passwords_by_category = list(
            passwords_qs
            .values('category')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        # Adicionar display name das categorias
        category_dict = dict(PASSWORD_CATEGORIES)
        for item in passwords_by_category:
            item['category_display'] = category_dict.get(item['category'], item['category'])

        # Atividades recentes (últimas 10) - filtrar por modelos de security
        security_models = ['Password', 'StoredCreditCard', 'StoredBankAccount', 'Archive']
        recent_activity = ActivityLog.objects.filter(
            user=user,
            model_name__in=security_models
        ).order_by('-created_at')[:10]

        recent_activity_data = []
        action_dict = dict(ACTION_TYPES)
        for log in recent_activity:
            recent_activity_data.append({
                'action': log.action,
                'action_display': action_dict.get(log.action, log.action),
                'model_name': log.model_name,
                'description': log.description,
                'created_at': log.created_at.isoformat()
            })

        stats = {
            'total_passwords': total_passwords,
            'total_stored_cards': total_stored_cards,
            'total_stored_accounts': total_stored_accounts,
            'total_archives': total_archives,
            'passwords_by_category': passwords_by_category,
            'recent_activity': recent_activity_data
        }

        return Response(stats)
