# --- Celery Configuration ---

# The list of modules to import when the Celery worker starts.
# This is how autodiscover_tasks() knows where to look.
# Add your app modules here.
CELERY_IMPORTS = [
    'web_scraper_app.run_tasks',
    'web_scraper_app.scraper.crawler',
    'web_scraper_app.scraper.filter',
    'web_scraper_app.scraper.retrieval',
]

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'

# Other optional settings
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# DJANGO CELERY BEAT
# Settings to allow 'django-celery-beat' to run migrations.

SECRET_KEY = "dummy-secret-key-for-migrations"

INSTALLED_APPS = (
    'django_celery_beat',
)

# Configure the database connection using the DATABASE_URL from the .env file
import os
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
}