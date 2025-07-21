from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_all_users),
    path('create/', views.create_user),
    path('update/<int:id>/', views.update_user),
    path('delete/<int:id>/', views.delete_user),
    path('test/', views.test_view),
]
