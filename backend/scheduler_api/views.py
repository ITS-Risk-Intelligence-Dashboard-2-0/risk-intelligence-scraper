from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth.models import User
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from .serializers import PeriodicTaskSerializer, IntervalScheduleSerializer, CrontabScheduleSerializer
from core.celery import app as celery_app
from scripts.seed_data import seed_data
import io
from contextlib import redirect_stdout
from celery.result import AsyncResult
from core.celery import app as celery_app
from shared.core_lib.source.models import Source
from shared.core_lib.source.serializers import SourceSerializer
import json

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

class TaskChoicesView(APIView):
    """
    An endpoint to provide a list of available Celery tasks.
    """
    def get(self, request, *args, **kwargs):
        try:
            tasks = list(sorted(celery_app.tasks.keys()))
            # Filter out internal Celery tasks for a cleaner list
            user_facing_tasks = [t for t in tasks if not t.startswith('celery.')]
            return Response(user_facing_tasks)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# A unique name for our manually triggered scraper task
MANUAL_SCRAPER_TASK_NAME = "manual_scraper_run"

class ScraperControlView(APIView):
    """
    Provides endpoints to start and stop the web scraping workflow.
    """
    permission_classes = [IsAdminUser] # Only admins can control the scraper

    def post(self, request, *args, **kwargs):
        """
        Starts the scraping workflow.
        """
        crawl_depth = request.data.get('crawl_depth', 1) # Default crawl depth to 1
        
        # Fetch active sources from the database
        active_sources = Source.objects.filter(is_active=True)
        if not active_sources.exists():
            return Response(
                {"status": "error", "message": "No active sources found. Please add at least one active source before starting."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sources_data = SourceSerializer(active_sources, many=True).data
        task_args = [sources_data, crawl_depth]

        try:
            # Create a default interval schedule (e.g., run every 1 day)
            # This is required by the model, even for a one-off task.
            interval, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.DAYS)

            # Create a disabled PeriodicTask to store the state and arguments
            PeriodicTask.objects.update_or_create(
                name=MANUAL_SCRAPER_TASK_NAME,
                defaults={
                    'task': 'web_scraper.tasks.start_scraping_workflow',
                    'interval': interval,
                    'enabled': False, # It's a one-off run, not scheduled
                    'one_off': True,
                    'args': json.dumps(task_args)
                }
            )

            # Send the task for immediate execution
            task_result = celery_app.send_task(
                'web_scraper.tasks.start_scraping_workflow',
                args=task_args
            )

            return Response(
                {"status": "success", "message": f"Scraping workflow started successfully with task ID: {task_result.id}"},
                status=status.HTTP_202_ACCEPTED
            )
        except Exception as e:
            return Response({"status": "error", "message": f"Failed to start scraping task: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, *args, **kwargs):
        """
        Stops a running scraping workflow by finding and revoking the task
        associated with the manual run.
        """
        try:
            task = PeriodicTask.objects.get(name=MANUAL_SCRAPER_TASK_NAME)
            
            # Find the active task by inspecting the workers.
            # This is a more advanced and reliable method than relying on session.
            inspector = celery_app.control.inspect()
            active_tasks = inspector.active()
            
            if not active_tasks:
                 return Response({"status": "info", "message": "No active workers found. The scraper may already be stopped."})

            task_revoked = False
            for worker, tasks in active_tasks.items():
                for active_task in tasks:
                    if active_task['name'] == task.task:
                        # Found the task, revoke it.
                        celery_app.control.revoke(active_task['id'], terminate=True)
                        task_revoked = True
            
            if task_revoked:
                 # Clean up the one-off task from the database
                task.delete()
                return Response({"status": "success", "message": "Stop signal sent to the running scraper task."})
            else:
                return Response({"status": "info", "message": "Scraper task is not currently running."})

        except PeriodicTask.DoesNotExist:
            return Response(
                {"status": "error", "message": "No manual scraping task has been run yet."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response({"status": "error", "message": f"Failed to stop task: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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