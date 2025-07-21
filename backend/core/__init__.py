# my_celery_scheduler_project_local/my_celery_scheduler_project/__init__.py

# This will make sure the app is always imported when Django starts so that shared_task will use this app.
from core.celery import app as celery_app # Corrected import path

__all__ = ('celery_app',)
