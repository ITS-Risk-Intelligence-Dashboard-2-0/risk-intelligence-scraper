# --- Celery Configuration ---

# The list of modules to import when the Celery worker starts.
# This is how autodiscover_tasks() knows where to look.
# Add your app modules here.
CELERY_IMPORTS = [
    'web_scraper_app.crawler.tasks',
    'web_scraper_app.scraper.tasks',
]

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'

# Other optional settings
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

CELERY_BEAT_SCHEDULE = {
    'define task here'
}