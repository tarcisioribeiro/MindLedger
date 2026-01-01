from django.contrib import admin
from personal_planning.models import (
    RoutineTask, DailyTaskRecord, Goal, DailyReflection
)


@admin.register(RoutineTask)
class RoutineTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'periodicity', 'is_active', 'owner')
    list_filter = ('category', 'periodicity', 'is_active')
    search_fields = ('name', 'description')


@admin.register(DailyTaskRecord)
class DailyTaskRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'date', 'completed', 'owner')
    list_filter = ('completed', 'date')
    search_fields = ('task__name', 'notes')


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'goal_type', 'status', 'current_value', 'target_value', 'owner')
    list_filter = ('goal_type', 'status')
    search_fields = ('title', 'description')


@admin.register(DailyReflection)
class DailyReflectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'mood', 'owner')
    list_filter = ('mood', 'date')
    search_fields = ('reflection',)
