from django.urls import path
from personal_planning.views import (
    # Dashboard
    PersonalPlanningDashboardStatsView,
    # Routine Tasks
    RoutineTaskListCreateView,
    RoutineTaskDetailView,
    # Daily Task Records
    DailyTaskRecordListCreateView,
    DailyTaskRecordDetailView,
    # Tasks for Today (special endpoint)
    TasksForTodayView,
    # Goals
    GoalListCreateView,
    GoalDetailView,
    # Daily Reflections
    DailyReflectionListCreateView,
    DailyReflectionDetailView,
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

    # Daily Task Records
    path('daily-records/', DailyTaskRecordListCreateView.as_view(),
         name='daily-task-record-list-create'),
    path('daily-records/<int:pk>/', DailyTaskRecordDetailView.as_view(),
         name='daily-task-record-detail'),

    # Tasks for Today (special)
    path('tasks-today/', TasksForTodayView.as_view(),
         name='tasks-for-today'),

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
]
