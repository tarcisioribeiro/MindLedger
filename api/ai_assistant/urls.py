from django.urls import path
from .views import AIQueryView, AIStreamingQueryView, AIStatusView

urlpatterns = [
    path('query/', AIQueryView.as_view(), name='ai-query'),  # Legacy endpoint (backward compatible)
    path('stream/', AIStreamingQueryView.as_view(), name='ai-stream'),  # New streaming endpoint
    path('status/', AIStatusView.as_view(), name='ai-status'),
]
