# my_celery_scheduler_project_local/my_celery_scheduler_project/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as authtoken_views
from scheduler_api import views as scheduler_views
from shared.core_lib.articles.views import ArticleViewSet
from shared.core_lib.source.views import SourceViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'periodic-tasks', scheduler_views.PeriodicTaskViewSet)
router.register(r'articles', ArticleViewSet)
router.register(r'sources', SourceViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/login/', authtoken_views.obtain_auth_token, name='api-login'),
    path('api/user/', scheduler_views.UserDetailView.as_view(), name='user-detail'),
    path('api/seed-data/', scheduler_views.SeedDataView.as_view(), name='seed-data'),
    path('api/task-choices/', scheduler_views.TaskChoicesView.as_view(), name='task-choices'),
    path('api/scraper/control/', scheduler_views.ScraperControlView.as_view(), name='scraper-control'),
]
