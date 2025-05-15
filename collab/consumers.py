import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import CollaborationSession, SessionParticipant, CollaborationAction, Comment
from AIcontent.models import Content

User = get_user_model()


class CollaborationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time collaboration.
    Handles document editing, cursor position updates, and comments.
    """
    async def connect(self):
        """
        Handle WebSocket connection. Validate the session and join the room.
        """
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'collab_session_{self.session_id}'
        self.user = self.scope['user']
        
        # Validate the session exists and user has permission
        session_valid = await self.validate_session()
        if not session_valid:
            await self.close()
            return
        
        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Update user presence
        await self.update_user_presence(True)
        
        # Send session information to the client
        session_info = await self.get_session_info()
        await self.send(text_data=json.dumps({
            'type': 'session_info',
            'data': session_info
        }))
        
        # Notify other participants that this user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection. Leave the room and update presence.
        """
        if hasattr(self, 'room_group_name'):
            # Update user presence
            await self.update_user_presence(False)
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            # Notify other participants that this user left
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'user_id': self.user.id,
                    'username': self.user.username
                }
            )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket and process based on message type.
        """
        data = json.loads(text_data)
        message_type = data.get('type', '')
        
        # Process different message types
        if message_type == 'update_content':
            await self.handle_content_update(data)
        elif message_type == 'cursor_position':
            await self.handle_cursor_position(data)
        elif message_type == 'add_comment':
            await self.handle_add_comment(data)
        elif message_type == 'resolve_comment':
            await self.handle_resolve_comment(data)
        elif message_type == 'presence_ping':
            await self.handle_presence_ping()
    
    async def handle_content_update(self, data):
        """
        Handle content updates from clients.
        Save the change to the database and broadcast to all participants.
        """
        content_data = data.get('content', {})
        position_start = content_data.get('position_start', 0)
        position_end = content_data.get('position_end', 0)
        content_before = content_data.get('content_before', '')
        content_after = content_data.get('content_after', '')
        
        # Create an action record in the database
        action = await self.create_action(
            action_type='EDIT',
            content_before=content_before,
            content_after=content_after,
            position_start=position_start,
            position_end=position_end,
            action_data=content_data
        )
        
        # Broadcast the content update to all clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'content_update',
                'user_id': self.user.id,
                'username': self.user.username,
                'content': content_data,
                'action_id': action.id if action else None,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def handle_cursor_position(self, data):
        """
        Handle cursor position updates from clients.
        Update the user's cursor position and broadcast to all participants.
        """
        position_data = data.get('position', {})
        
        # Update the user's cursor position in the database
        await self.update_cursor_position(position_data)
        
        # Broadcast the cursor position to all clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'cursor_position',
                'user_id': self.user.id,
                'username': self.user.username,
                'position': position_data
            }
        )
    
    async def handle_add_comment(self, data):
        """
        Handle adding a new comment.
        Create the comment in the database and broadcast to all participants.
        """
        comment_text = data.get('text', '')
        position = data.get('position', {})
        
        # Create a comment in the database
        comment = await self.create_comment(comment_text, position)
        
        # Broadcast the comment to all clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'new_comment',
                'comment_id': comment.id if comment else None,
                'user_id': self.user.id,
                'username': self.user.username,
                'text': comment_text,
                'position': position,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def handle_resolve_comment(self, data):
        """
        Handle resolving a comment.
        Update the comment in the database and broadcast to all participants.
        """
        comment_id = data.get('comment_id', None)
        
        # Resolve the comment in the database
        success = await self.resolve_comment(comment_id)
        
        if success:
            # Broadcast the resolution to all clients
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'comment_resolved',
                    'comment_id': comment_id,
                    'resolved_by_id': self.user.id,
                    'resolved_by': self.user.username,
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    async def handle_presence_ping(self):
        """
        Handle presence ping from clients.
        Update the last activity time for the user.
        """
        await self.update_user_activity()
    
    # Message handlers for broadcasts
    
    async def content_update(self, event):
        """Send content update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'content_update',
            'user_id': event['user_id'],
            'username': event['username'],
            'content': event['content'],
            'action_id': event['action_id'],
            'timestamp': event['timestamp']
        }))
    
    async def cursor_position(self, event):
        """Send cursor position update to WebSocket."""
        # Don't send cursor updates back to the same user who sent them
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'cursor_position',
                'user_id': event['user_id'],
                'username': event['username'],
                'position': event['position']
            }))
    
    async def new_comment(self, event):
        """Send new comment notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'new_comment',
            'comment_id': event['comment_id'],
            'user_id': event['user_id'],
            'username': event['username'],
            'text': event['text'],
            'position': event['position'],
            'timestamp': event['timestamp']
        }))
    
    async def comment_resolved(self, event):
        """Send comment resolved notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'comment_resolved',
            'comment_id': event['comment_id'],
            'resolved_by_id': event['resolved_by_id'],
            'resolved_by': event['resolved_by'],
            'timestamp': event['timestamp']
        }))
    
    async def user_join(self, event):
        """Send user join notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'user_join',
            'user_id': event['user_id'],
            'username': event['username']
        }))
    
    async def user_leave(self, event):
        """Send user leave notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'user_leave',
            'user_id': event['user_id'],
            'username': event['username']
        }))
    
    # Database access methods (sync to async)
    
    @database_sync_to_async
    def validate_session(self):
        """Validate that the session exists and user has permission to join."""
        try:
            session = CollaborationSession.objects.get(id=self.session_id)
            if not session.is_active():
                return False
            
            # Create participant if not exists
            if not session.participants.filter(id=self.user.id).exists():
                if not session.can_join(self.user):
                    return False
                session.add_participant(self.user)
            
            return True
        except CollaborationSession.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_session_info(self):
        """Get information about the current session for the client."""
        try:
            session = CollaborationSession.objects.get(id=self.session_id)
            content = session.content
            
            # Get participants info
            participants = []
            for participant in session.sessionparticipant_set.select_related('user').all():
                participants.append({
                    'id': participant.user.id,
                    'username': participant.user.username,
                    'role': participant.role,
                    'is_present': participant.is_present,
                    'cursor_position': participant.cursor_position
                })
            
            # Get comments info
            comments = []
            for comment in session.comments.select_related('user').all():
                comments.append({
                    'id': comment.id,
                    'user_id': comment.user.id,
                    'username': comment.user.username,
                    'text': comment.text,
                    'position': comment.position,
                    'is_resolved': comment.is_resolved,
                    'created_at': comment.created_at.isoformat()
                })
            
            return {
                'session_id': session.id,
                'content_id': content.id,
                'content_title': content.title,
                'content_body': content.body if hasattr(content, 'body') else '',
                'participants': participants,
                'comments': comments,
                'created_by': session.created_by.username,
                'created_at': session.created_at.isoformat(),
                'status': session.status
            }
        
        except CollaborationSession.DoesNotExist:
            return {}
    
    @database_sync_to_async
    def update_user_presence(self, is_present):
        """Update the user's presence status."""
        try:
            participant = SessionParticipant.objects.get(
                session_id=self.session_id,
                user_id=self.user.id
            )
            participant.set_presence(is_present)
            return True
        except SessionParticipant.DoesNotExist:
            return False
    
    @database_sync_to_async
    def update_user_activity(self):
        """Update the user's last activity timestamp."""
        try:
            participant = SessionParticipant.objects.get(
                session_id=self.session_id,
                user_id=self.user.id
            )
            participant.last_active = timezone.now()
            participant.save(update_fields=['last_active'])
            return True
        except SessionParticipant.DoesNotExist:
            return False
    
    @database_sync_to_async
    def update_cursor_position(self, position_data):
        """Update the user's cursor position."""
        try:
            participant = SessionParticipant.objects.get(
                session_id=self.session_id,
                user_id=self.user.id
            )
            participant.update_cursor(position_data)
            return True
        except SessionParticipant.DoesNotExist:
            return False
    
    @database_sync_to_async
    def create_action(self, action_type, content_before='', content_after='', 
                      position_start=0, position_end=0, action_data=None):
        """Create a new collaboration action record."""
        try:
            session = CollaborationSession.objects.get(id=self.session_id)
            action = CollaborationAction.objects.create(
                session=session,
                user=self.user,
                action_type=action_type,
                content_before=content_before,
                content_after=content_after,
                position_start=position_start,
                position_end=position_end,
                action_data=action_data or {}
            )
            return action
        except CollaborationSession.DoesNotExist:
            return None
    
    @database_sync_to_async
    def create_comment(self, text, position):
        """Create a new comment."""
        try:
            session = CollaborationSession.objects.get(id=self.session_id)
            comment = Comment.objects.create(
                session=session,
                user=self.user,
                text=text,
                position=position
            )
            return comment
        except CollaborationSession.DoesNotExist:
            return None
    
    @database_sync_to_async
    def resolve_comment(self, comment_id):
        """Resolve a comment."""
        try:
            comment = Comment.objects.get(id=comment_id, session_id=self.session_id)
            comment.resolve(self.user)
            return True
        except Comment.DoesNotExist:
            return False