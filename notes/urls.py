from django.urls import path
from . import views


urlpatterns = [
    path('list/', views.NoteList.as_view(), name='notes_list'),
    path('create/', views.NoteCreate.as_view(), name='note_create'),
    path("details/<slug:slug>/", views.NoteDetail.as_view(), name='note-detail'),
    path("update/<slug:slug>/", views.NoteUpdate.as_view(), name='note-update'),
    path("delete/<slug:slug>/", views.NoteDelete.as_view(), name='note-delete'),
    path("create_comment/", views.create_comment, name='create_comment'),

]