# from django.shortcuts import render

# # Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import uuid

from .models import CollaborationSession, SessionParticipant, CollaborationAction, Comment
from AIcontent.models import Content


@login_required
def collaboration_dashboard(request):
    """
    Display a dashboard of collaboration sessions for the user.
    """
    # Get sessions where the user is a participant
    user_sessions = CollaborationSession.objects.filter(
        participants=request.user
    ).order_by('-updated_at')
    
    # Get sessions the user created
    created_sessions = CollaborationSession.objects.filter(
        created_by=request.user
    ).order_by('-updated_at')
    
    # Combine and remove duplicates
    all_sessions = list(created_sessions)
    for session in user_sessions:
        if session not in all_sessions:
            all_sessions.append(session)
    
    context = {
        'sessions': all_sessions,
        'active_sessions': [s for s in all_sessions if s.status == 'ACTIVE'],
        'completed_sessions': [s for s in all_sessions if s.status == 'COMPLETED'],
    }
    
    return render(request, 'collab/dashboard.html', context)


@login_required
def session_detail(request, session_id):
    """
    Display a collaboration session interface.
    """
    session = get_object_or_404(CollaborationSession, id=session_id)
    
    # Check if user is a participant or has permission to view
    if not session.participants.filter(id=request.user.id).exists():
        if not session.is_public:
            # Add user as participant if the session is active and can join
            if session.is_active() and session.can_join(request.user):
                session.add_participant(request.user)
            else:
                # Redirect to dashboard with error message
                return redirect('collab:dashboard')
    
    # Get session information
    participants = session.sessionparticipant_set.select_related('user').all()
    comments = session.comments.select_related('user').all()
    
    context = {
        'session': session,
        'content': session.content,
        'participants': participants,
        'comments': comments,
        'user_role': session.sessionparticipant_set.get(user=request.user).role,
    }
    
    return render(request, 'collab/session.html', context)


@login_required
@require_http_methods(['POST'])
def create_session(request):
    """
    Create a new collaboration session.
    """
    try:
        data = json.loads(request.body)
        content_id = data.get('content_id')
        title = data.get('title', '')
        
        content = get_object_or_404(Content, id=content_id)
        
        # Check if user has permission to create a session for this content
        # This would depend on your permission model
        
        # Create a unique join code
        join_code = str(uuid.uuid4())[:8]
        
        # Create the session
        session = CollaborationSession.objects.create(
            content=content,
            created_by=request.user,
            title=title or f"Collaboration on {content.title}",
            join_code=join_code
        )
        
        # Add the creator as a session leader
        SessionParticipant.objects.create(
            session=session,
            user=request.user,
            role='LEADER'
        )
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'join_code': session.join_code
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(['POST'])
def join_session(request):
    """
    Join a collaboration session using a join code.
    """
    try:
        data = json.loads(request.body)
        join_code = data.get('join_code')
        
        session = get_object_or_404(CollaborationSession, join_code=join_code)
        
        # Check if session is active and user can join
        if not session.is_active():
            return JsonResponse({
                'success': False,
                'error': 'This session is no longer active.'
            }, status=400)
        
        if not session.can_join(request.user):
            return JsonResponse({
                'success': False,
                'error': 'You cannot join this session.'
            }, status=403)
        
        # Add user as participant
        participant = session.add_participant(request.user)
        
        return JsonResponse({
            'success': True,
            'session_id': session.id
        })
        
    except CollaborationSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Invalid join code.'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(['POST'])
def end_session(request, session_id):
    """
    End a collaboration session.
    """
    session = get_object_or_404(CollaborationSession, id=session_id)
    
    # Check if user is the session creator or has permission
    if request.user != session.created_by and not request.user.is_staff:
        participant = session.sessionparticipant_set.filter(user=request.user).first()
        if not participant or participant.role != 'LEADER':
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to end this session.'
            }, status=403)
    
    # Update session status
    session.status = 'COMPLETED'
    session.end_time = timezone.now()
    session.save()
    
    # Log the end session action
    CollaborationAction.objects.create(
        session=session,
        user=request.user,
        action_type='END_SESSION',
        description=f"Session ended by {request.user.username}"
    )
    
    return JsonResponse({
        'success': True,
        'session_id': session.id
    })


@login_required
@require_http_methods(['POST'])
def add_comment(request, session_id):
    """
    Add a comment to a collaboration session.
    """
    session = get_object_or_404(CollaborationSession, id=session_id)
    
    # Check if user is a participant
    if not session.participants.filter(id=request.user.id).exists():
        return JsonResponse({
            'success': False,
            'error': 'You are not a participant in this session.'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        text = data.get('text')
        content_reference = data.get('content_reference', None)
        
        if not text:
            return JsonResponse({
                'success': False,
                'error': 'Comment text is required.'
            }, status=400)
        
        # Create the comment
        comment = Comment.objects.create(
            session=session,
            user=request.user,
            text=text,
            content_reference=content_reference
        )
        
        # Update session's updated_at timestamp
        session.updated_at = timezone.now()
        session.save()
        
        return JsonResponse({
            'success': True,
            'comment_id': comment.id,
            'user': comment.user.username,
            'text': comment.text,
            'created_at': comment.created_at.isoformat(),
            'content_reference': comment.content_reference
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(['DELETE'])
def delete_comment(request, comment_id):
    """
    Delete a comment from a collaboration session.
    """
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Check if user is the comment author or has permission
    if request.user != comment.user and request.user != comment.session.created_by:
        participant = comment.session.sessionparticipant_set.filter(user=request.user).first()
        if not participant or participant.role != 'LEADER':
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to delete this comment.'
            }, status=403)
    
    # Delete the comment
    comment.delete()
    
    return JsonResponse({
        'success': True
    })


@login_required
@require_http_methods(['POST'])
def record_action(request, session_id):
    """
    Record a collaboration action.
    """
    session = get_object_or_404(CollaborationSession, id=session_id)
    
    # Check if user is a participant
    if not session.participants.filter(id=request.user.id).exists():
        return JsonResponse({
            'success': False,
            'error': 'You are not a participant in this session.'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        action_type = data.get('action_type')
        description = data.get('description')
        content_reference = data.get('content_reference', None)
        
        if not action_type or not description:
            return JsonResponse({
                'success': False,
                'error': 'Action type and description are required.'
            }, status=400)
        
        # Record the action
        action = CollaborationAction.objects.create(
            session=session,
            user=request.user,
            action_type=action_type,
            description=description,
            content_reference=content_reference
        )
        
        # Update session's updated_at timestamp
        session.updated_at = timezone.now()
        session.save()
        
        return JsonResponse({
            'success': True,
            'action_id': action.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(['POST'])
def change_participant_role(request, session_id, participant_id):
    """
    Change a participant's role in the session.
    """
    session = get_object_or_404(CollaborationSession, id=session_id)
    participant = get_object_or_404(SessionParticipant, id=participant_id, session=session)
    
    # Check if the requesting user is the session creator or a leader
    if request.user != session.created_by:
        requester = session.sessionparticipant_set.filter(user=request.user).first()
        if not requester or requester.role != 'LEADER':
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to change roles.'
            }, status=403)
    
    try:
        data = json.loads(request.body)
        new_role = data.get('role')
        
        if new_role not in ['LEADER', 'EDITOR', 'VIEWER']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid role.'
            }, status=400)
        
        # Update the role
        participant.role = new_role
        participant.save()
        
        # Log the action
        CollaborationAction.objects.create(
            session=session,
            user=request.user,
            action_type='CHANGE_ROLE',
            description=f"Changed {participant.user.username}'s role to {new_role}"
        )
        
        return JsonResponse({
            'success': True,
            'participant_id': participant.id,
            'role': participant.role
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(['POST'])
def remove_participant(request, session_id, participant_id):
    """
    Remove a participant from the session.
    """
    session = get_object_or_404(CollaborationSession, id=session_id)
    participant = get_object_or_404(SessionParticipant, id=participant_id, session=session)
    
    # Check if the requesting user is the session creator or a leader
    if request.user != session.created_by:
        requester = session.sessionparticipant_set.filter(user=request.user).first()
        if not requester or requester.role != 'LEADER':
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to remove participants.'
            }, status=403)
    
    # Cannot remove the session creator
    if participant.user == session.created_by:
        return JsonResponse({
            'success': False,
            'error': 'Cannot remove the session creator.'
        }, status=400)
    
    # Log the action before deletion
    removed_username = participant.user.username
    
    # Remove the participant
    participant.delete()
    
    # Log the action
    CollaborationAction.objects.create(
        session=session,
        user=request.user,
        action_type='REMOVE_PARTICIPANT',
        description=f"Removed {removed_username} from the session"
    )
    
    return JsonResponse({
        'success': True
    })


@login_required
@require_http_methods(['GET'])
def get_session_history(request, session_id):
    """
    Get the history of actions for a session.
    """
    session = get_object_or_404(CollaborationSession, id=session_id)
    
    # Check if user is a participant
    if not session.participants.filter(id=request.user.id).exists():
        return JsonResponse({
            'success': False,
            'error': 'You are not a participant in this session.'
        }, status=403)
    
    # Get all actions for this session
    actions = CollaborationAction.objects.filter(
        session=session
    ).select_related('user').order_by('created_at')
    
    # Format the actions
    action_list = []
    for action in actions:
        action_list.append({
            'id': action.id,
            'user': action.user.username,
            'action_type': action.action_type,
            'description': action.description,
            'content_reference': action.content_reference,
            'created_at': action.created_at.isoformat()
        })
    
    return JsonResponse({
        'success': True,
        'actions': action_list
    })