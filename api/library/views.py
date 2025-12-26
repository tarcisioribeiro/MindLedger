from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from app.permissions import GlobalDefaultPermission
from library.models import Author, Publisher, Book, Summary, Reading
from library.serializers import (
    AuthorSerializer, AuthorCreateUpdateSerializer,
    PublisherSerializer, PublisherCreateUpdateSerializer,
    BookSerializer, BookCreateUpdateSerializer,
    SummarySerializer, SummaryCreateUpdateSerializer,
    ReadingSerializer, ReadingCreateUpdateSerializer
)


def log_activity(request, action, model_name, object_id, description):
    """Helper para registrar atividades de biblioteca."""
    try:
        from security.activity_logs.models import ActivityLog
        ActivityLog.log_action(
            user=request.user,
            action=action,
            description=description,
            model_name=model_name,
            object_id=object_id,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    except:
        pass  # Se ActivityLog não estiver disponível, ignora


def get_client_ip(request):
    """Extrai o IP do cliente da requisição."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================================================
# AUTHOR VIEWS
# ============================================================================

class AuthorListCreateView(generics.ListCreateAPIView):
    """Lista todos os autores ou cria um novo."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Author.objects.all()

    def get_queryset(self):
        return Author.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner').prefetch_related('books')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AuthorCreateUpdateSerializer
        return AuthorSerializer

    def perform_create(self, serializer):
        author = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            self.request,
            'create',
            'Author',
            author.id,
            f'Criou autor: {author.name}'
        )


class AuthorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, atualiza ou deleta um autor."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Author.objects.all()

    def get_queryset(self):
        return Author.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner').prefetch_related('books')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AuthorCreateUpdateSerializer
        return AuthorSerializer

    def perform_update(self, serializer):
        author = serializer.save(updated_by=self.request.user)
        log_activity(
            self.request,
            'update',
            'Author',
            author.id,
            f'Atualizou autor: {author.name}'
        )

    def perform_destroy(self, instance):
        instance.deleted_at = instance.updated_at
        instance.deleted_by = self.request.user
        instance.save()
        log_activity(
            self.request,
            'delete',
            'Author',
            instance.id,
            f'Deletou autor: {instance.name}'
        )


# ============================================================================
# PUBLISHER VIEWS
# ============================================================================

class PublisherListCreateView(generics.ListCreateAPIView):
    """Lista todas as editoras ou cria uma nova."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Publisher.objects.all()

    def get_queryset(self):
        return Publisher.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner').prefetch_related('books')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PublisherCreateUpdateSerializer
        return PublisherSerializer

    def perform_create(self, serializer):
        publisher = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            self.request,
            'create',
            'Publisher',
            publisher.id,
            f'Criou editora: {publisher.name}'
        )


class PublisherDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, atualiza ou deleta uma editora."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Publisher.objects.all()

    def get_queryset(self):
        return Publisher.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner').prefetch_related('books')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PublisherCreateUpdateSerializer
        return PublisherSerializer

    def perform_update(self, serializer):
        publisher = serializer.save(updated_by=self.request.user)
        log_activity(
            self.request,
            'update',
            'Publisher',
            publisher.id,
            f'Atualizou editora: {publisher.name}'
        )

    def perform_destroy(self, instance):
        instance.deleted_at = instance.updated_at
        instance.deleted_by = self.request.user
        instance.save()
        log_activity(
            self.request,
            'delete',
            'Publisher',
            instance.id,
            f'Deletou editora: {instance.name}'
        )


# ============================================================================
# BOOK VIEWS
# ============================================================================

class BookListCreateView(generics.ListCreateAPIView):
    """Lista todos os livros ou cria um novo."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Book.objects.all()

    def get_queryset(self):
        return Book.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'publisher').prefetch_related('authors', 'readings')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BookCreateUpdateSerializer
        return BookSerializer

    def perform_create(self, serializer):
        book = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            self.request,
            'create',
            'Book',
            book.id,
            f'Criou livro: {book.title}'
        )


class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, atualiza ou deleta um livro."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Book.objects.all()

    def get_queryset(self):
        return Book.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'publisher').prefetch_related('authors', 'readings')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return BookCreateUpdateSerializer
        return BookSerializer

    def perform_update(self, serializer):
        book = serializer.save(updated_by=self.request.user)
        log_activity(
            self.request,
            'update',
            'Book',
            book.id,
            f'Atualizou livro: {book.title}'
        )

    def perform_destroy(self, instance):
        instance.deleted_at = instance.updated_at
        instance.deleted_by = self.request.user
        instance.save()
        log_activity(
            self.request,
            'delete',
            'Book',
            instance.id,
            f'Deletou livro: {instance.title}'
        )


# ============================================================================
# SUMMARY VIEWS
# ============================================================================

class SummaryListCreateView(generics.ListCreateAPIView):
    """Lista todos os resumos ou cria um novo."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Summary.objects.all()

    def get_queryset(self):
        return Summary.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'book')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SummaryCreateUpdateSerializer
        return SummarySerializer

    def perform_create(self, serializer):
        summary = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            self.request,
            'create',
            'Summary',
            summary.id,
            f'Criou resumo: {summary.title}'
        )


class SummaryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, atualiza ou deleta um resumo."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Summary.objects.all()

    def get_queryset(self):
        return Summary.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'book')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SummaryCreateUpdateSerializer
        return SummarySerializer

    def perform_update(self, serializer):
        summary = serializer.save(updated_by=self.request.user)
        log_activity(
            self.request,
            'update',
            'Summary',
            summary.id,
            f'Atualizou resumo: {summary.title}'
        )

    def perform_destroy(self, instance):
        instance.deleted_at = instance.updated_at
        instance.deleted_by = self.request.user
        instance.save()
        log_activity(
            self.request,
            'delete',
            'Summary',
            instance.id,
            f'Deletou resumo: {instance.title}'
        )


# ============================================================================
# READING VIEWS
# ============================================================================

class ReadingListCreateView(generics.ListCreateAPIView):
    """Lista todas as leituras ou cria uma nova."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Reading.objects.all()

    def get_queryset(self):
        return Reading.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'book')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReadingCreateUpdateSerializer
        return ReadingSerializer

    def perform_create(self, serializer):
        reading = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            self.request,
            'create',
            'Reading',
            reading.id,
            f'Registrou leitura de: {reading.book.title}'
        )


class ReadingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, atualiza ou deleta uma leitura."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Reading.objects.all()

    def get_queryset(self):
        return Reading.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'book')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ReadingCreateUpdateSerializer
        return ReadingSerializer

    def perform_update(self, serializer):
        reading = serializer.save(updated_by=self.request.user)
        log_activity(
            self.request,
            'update',
            'Reading',
            reading.id,
            f'Atualizou leitura de: {reading.book.title}'
        )

    def perform_destroy(self, instance):
        instance.deleted_at = instance.updated_at
        instance.deleted_by = self.request.user
        instance.save()
        log_activity(
            self.request,
            'delete',
            'Reading',
            instance.id,
            f'Deletou leitura de: {instance.book.title}'
        )
