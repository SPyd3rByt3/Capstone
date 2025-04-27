from django.urls import path
from . import views


urlpatterns = [
    path('list/', views.NoteList.as_view(), name='notes_list'),
    path('create/', views.NoteCreate.as_view(), name='note_create'),
    path("details/<int:pk>/", views.NoteDetail.as_view(), name='note-detail'),
    path("update/<int:pk>/", views.NoteUpdate.as_view(), name='note-update'),
    path("delete/<int:pk>/", views.NoteDelete.as_view(), name='note-delete'),

]