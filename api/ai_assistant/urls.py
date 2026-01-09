from django.urls import path
from .views import AIQueryView, AIStatusView

urlpatterns = [
    path('query/', AIQueryView.as_view(), name='ai-query'),
    path('status/', AIStatusView.as_view(), name='ai-status'),
]
