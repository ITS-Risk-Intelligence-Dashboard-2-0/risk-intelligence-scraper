from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from celery.exceptions import CeleryError
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from .serializers import PeriodicTaskSerializer, IntervalScheduleSerializer, CrontabScheduleSerializer
from core.celery import app as celery_app 

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