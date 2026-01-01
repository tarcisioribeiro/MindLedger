from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app.health import health_check, ready_check, live_check

urlpatterns = [
    path("admin/", admin.site.urls),
    # Health check endpoints
    path('health/', health_check, name='health-check'),
    path('ready/', ready_check, name='ready-check'),
    path('live/', live_check, name='live-check'),
    # API endpoints
    path('api/v1/', include('authentication.urls')),
    path('api/v1/', include('accounts.urls')),
    path('api/v1/', include('credit_cards.urls')),
    path('api/v1/', include('expenses.urls')),
    path('api/v1/', include('loans.urls')),
    path('api/v1/', include('members.urls')),
    path('api/v1/', include('revenues.urls')),
    path('api/v1/', include('transfers.urls')),
    path('api/v1/dashboard/', include('dashboard.urls')),
    # Security Module
    path('api/v1/security/', include('security.urls')),
    # Library Module
    path('api/v1/library/', include('library.urls')),
    # AI Assistant
    path('api/v1/ai/', include('ai_assistant.urls')),
    # Personal Planning Module
    path('api/v1/personal-planning/', include('personal_planning.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
