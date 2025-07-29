import os
import sys
from celery import Celery

sys.path.insert(0, "/app")
app = Celery('web_scraper_project')

app.config_from_object('web_scraper_project.settings', namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
