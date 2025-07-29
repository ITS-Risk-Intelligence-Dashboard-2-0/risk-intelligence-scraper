from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from celery.exceptions import CeleryError
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from .serializers import PeriodicTaskSerializer, IntervalScheduleSerializer, CrontabScheduleSerializer
from core.celery import app as celery_app 
from scripts.seed_data import seed_data
import io
from contextlib import redirect_stdout

class PeriodicTaskViewSet(viewsets.ModelViewSet):
    queryset = PeriodicTask.objects.all()
    serializer_class = PeriodicTaskSerializer

class IntervalScheduleViewSet(viewsets.ModelViewSet):
    queryset = IntervalSchedule.objects.all()
    serializer_class = IntervalScheduleSerializer

class CrontabScheduleViewSet(viewsets.ModelViewSet):
    queryset = CrontabSchedule.objects.all()
    serializer_class = CrontabScheduleSerializer

class RegisteredTasksView(APIView):
    def get(self, request, *args, **kwargs):
        """
        Inspects running Celery workers to discover registered tasks.
        """
        try:
            inspector = celery_app.control.inspect()
            
            # The .registered() method returns a dictionary where keys are worker names
            # and values are lists of registered task names.
            # E.g., {'celery@worker1': ['task1', 'task2'], 'celery@worker2': ['task1', 'task2']}
            registered_tasks_by_worker = inspector.registered()

            if not registered_tasks_by_worker:
                # This can happen if no workers are running or they haven't responded yet.
                return Response({"error": "No running Celery workers found or they are not responding."}, status=503)

            # We can collect all tasks from all workers and get a unique, sorted list.
            all_tasks = set()
            for worker_tasks in registered_tasks_by_worker.values():
                for task in worker_tasks:
                    if not task.startswith('celery.'):
                        all_tasks.add(task)

            return Response(sorted(list(all_tasks)))

        except CeleryError as e:
            return Response({"error": f"Could not connect to the message broker: {e}"}, status=503)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class SeedDataView(APIView):
    """
    An endpoint for administrators to seed the database with test data.
    """
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        try:
            # Capture the print output from the script to return as a log
            f = io.StringIO()
            with redirect_stdout(f):
                seed_data()
            output = f.getvalue()
            
            return Response({"status": "success", "log": output}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserDetailView(APIView):
    """
    Provides details for the currently authenticated user.
    """
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response({
                'username': request.user.username,
                'email': request.user.email,
                'is_staff': request.user.is_staff, # is_staff for admin role
            })
        return Response({'error': 'Not authenticated'}, status=401)