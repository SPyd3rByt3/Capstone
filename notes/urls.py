from django.urls import path
from . import views


urlpatterns = [
    path('list/', views.NoteList.as_view(), name='notes_list'),
    path('create/', views.NoteCreate.as_view(), name='note_create'),

]