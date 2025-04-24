from django.urls import path
from . import views

from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.projects_list_view, name='projects_list'),
    # path('delete/<int:pk>/', views.project_delete, name='project_delete'),
    path('new/', views.project_new_view, name='project_new'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # for media files