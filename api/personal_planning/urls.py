from django.urls import path
from personal_planning.views import (
    # Dashboard
    PersonalPlanningDashboardStatsView,
    # Routine Tasks
    RoutineTaskListCreateView,
    RoutineTaskDetailView,
    # Goals
    GoalListCreateView,
    GoalDetailView,
    # Daily Reflections
    DailyReflectionListCreateView,
    DailyReflectionDetailView,
    # Task Instances
    TaskInstanceListCreateView,
    TaskInstanceDetailView,
    InstancesForDateView,
    TaskInstanceStatusUpdateView,
    TaskInstanceBulkUpdateView,
)

urlpatterns = [
    # Dashboard
    path('dashboard/stats/', PersonalPlanningDashboardStatsView.as_view(),
         name='personal-planning-dashboard-stats'),

    # Routine Tasks
    path('routine-tasks/', RoutineTaskListCreateView.as_view(),
         name='routine-task-list-create'),
    path('routine-tasks/<int:pk>/', RoutineTaskDetailView.as_view(),
         name='routine-task-detail'),

    # Goals
    path('goals/', GoalListCreateView.as_view(),
         name='goal-list-create'),
    path('goals/<int:pk>/', GoalDetailView.as_view(),
         name='goal-detail'),

    # Daily Reflections
    path('reflections/', DailyReflectionListCreateView.as_view(),
         name='daily-reflection-list-create'),
    path('reflections/<int:pk>/', DailyReflectionDetailView.as_view(),
         name='daily-reflection-detail'),

    # Task Instances
    path('instances/', TaskInstanceListCreateView.as_view(),
         name='task-instance-list-create'),
    path('instances/<int:pk>/', TaskInstanceDetailView.as_view(),
         name='task-instance-detail'),
    path('instances/for-date/', InstancesForDateView.as_view(),
         name='instances-for-date'),
    path('instances/<int:pk>/status/', TaskInstanceStatusUpdateView.as_view(),
         name='task-instance-status-update'),
    path('instances/bulk-update/', TaskInstanceBulkUpdateView.as_view(),
         name='task-instance-bulk-update'),
]
