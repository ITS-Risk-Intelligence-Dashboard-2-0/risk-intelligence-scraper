# Register celery beat for django admin

from django.contrib import admin
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule

@admin.register(PeriodicTask)
class PeriodicTaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'task', 'enabled', 'interval', 'crontab', 'one_off', 'start_time', 'expires', 'last_run_at', 'total_run_count')
    list_filter = ('enabled', 'one_off', 'task')
    search_fields = ('name', 'task', 'description')
    raw_id_fields = ('interval', 'crontab')

@admin.register(CrontabSchedule)
class CrontabScheduleAdmin(admin.ModelAdmin):
    list_display = ('minute', 'hour', 'day_of_week', 'day_of_month', 'month_of_year', 'timezone')
    search_fields = ('minute', 'hour', 'day_of_week', 'day_of_month', 'month_of_year', 'timezone')

@admin.register(IntervalSchedule)
class IntervalScheduleAdmin(admin.ModelAdmin):
    list_display = ('every', 'period')
    search_fields = ('every', 'period')
