# Define the url patterns
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PeriodicTaskViewSet #, CrontabScheduleViewSet, IntervalScheduleViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'periodic_tasks', PeriodicTaskViewSet)
# Uncomment these if you decide to expose direct API endpoints for schedules
# router.register(r'crontab_schedules', CrontabScheduleViewSet)
# router.register(r'interval_schedules', IntervalScheduleViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
