from django.urls import path
from . import views

app_name = 'collab'

urlpatterns = [
    path('', views.collaboration_dashboard, name='dashboard'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('session/create/', views.create_session, name='create_session'),
    path('session/join/', views.join_session, name='join_session'),
    path('session/<int:session_id>/end/', views.end_session, name='end_session'),
    path('session/<int:session_id>/add_comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('session/<int:session_id>/record_action/', views.record_action, name='record_action'),
    path('session/<int:session_id>/change_role/<int:participant_id>/', views.change_participant_role, name='change_participant_role'),
    path('session/<int:session_id>/remove_participant/<int:participant_id>/', views.remove_participant, name='remove_participant'),
    path('session/<int:session_id>/history/', views.get_session_history, name='get_session_history'),
]
