from django.urls import path
from .views import DashboardStatsView, AccountBalancesView

urlpatterns = [
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('account-balances/', AccountBalancesView.as_view(), name='account-balances'),
]
