# my_celery_scheduler_project_local/my_celery_scheduler_project/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from scheduler_api.views import UserDetailView, SeedDataView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('scheduler_api.urls')),
    path('api/login/', obtain_auth_token, name='api_token_auth'),
    path('api/user/', UserDetailView.as_view(), name='user-detail'),
    path('api/seed-data/', SeedDataView.as_view(), name='seed-data'),
    path('api/articles/', include('shared.core_lib.articles.urls'))

]
