# schedule_api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PeriodicTaskViewSet,
    IntervalScheduleViewSet,
    CrontabScheduleViewSet,
    RegisteredTasksView
)

router = DefaultRouter()
router.register(r'periodic-tasks', PeriodicTaskViewSet)
router.register(r'intervals', IntervalScheduleViewSet)
router.register(r'crontabs', CrontabScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('registered-tasks/', RegisteredTasksView.as_view(), name='registered-tasks'),
]