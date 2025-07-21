# Define API endpoints for scheduler_api
from rest_framework import viewsets
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
from .serializers import PeriodicTaskSerializer, CrontabScheduleSerializer, IntervalScheduleSerializer
from rest_framework.permissions import IsAuthenticated

class PeriodicTaskViewSet(viewsets.ModelViewSet):
    queryset = PeriodicTask.objects.all().select_related('crontab', 'interval')
    serializer_class = PeriodicTaskSerializer
    lookup_field = 'name'
    permission_classes = [IsAuthenticated]
