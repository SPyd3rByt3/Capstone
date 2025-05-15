import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Content, ContentVersion
from django.contrib.auth import get_user_model

User = get_user_model()

class ContentCollaborationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.content_id = self.scope['url_route']['kwargs']['content_id']
        self.room_group_name = f'content_{self.content_id}'
        self.user = self.scope['user']
        
        # Verify that the user has permission to access this content
        if not await self.has_content_access():
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send user joined message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'username': self.user.username,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Send user left message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id,
                'username': self.user.username,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def receive(self, text_data):
        """
        Receive message from WebSocket
        """
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        # Handle different message types
        if message_type == 'content_update':
            await self.handle_content_update(text_data_json)
        elif message_type == 'cursor_position':
            await self.handle_cursor_position(text_data_json)
        elif message_type == 'save_version':
            await self.handle_save_version(text_data_json)
        elif message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)

    async def handle_content_update(self, data):
        """
        Handle content updates from clients
        """
        # Forward the update to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'content_update',
                'user_id': self.user.id,
                'username': self.user.username,
                'content': data.get('content'),
                'position': data.get('position'),
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_cursor_position(self, data):
        """
        Handle cursor position updates
        """
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'cursor_position',
                'user_id': self.user.id,
                'username': self.user.username,
                'position': data.get('position'),
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_save_version(self, data):
        """
        Save a new version of the content
        """
        try:
            content_data = data.get('content')
            comment = data.get('comment', '')
            
            # Save version to database
            version = await self.save_content_version(content_data, comment)
            
            # Notify the group that a new version was saved
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'version_saved',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'version_number': version.version_number,
                    'comment': comment,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            # Send error message
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def handle_chat_message(self, data):
        """
        Handle collaboration chat messages
        """
        message = data.get('message', '')
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'user_id': self.user.id,
                'username': self.user.username,
                'message': message,
                'timestamp': timezone.now().isoformat()
            }
        )

    # Methods for sending messages to WebSocket
    async def content_update(self, event):
        """
        Send content update to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'content_update',
            'user_id': event['user_id'],
            'username': event['username'],
            'content': event['content'],
            'position': event['position'],
            'timestamp': event['timestamp']
        }))

    async def cursor_position(self, event):
        """
        Send cursor position to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'cursor_position',
            'user_id': event['user_id'],
            'username': event['username'],
            'position': event['position'],
            'timestamp': event['timestamp']
        }))

    async def version_saved(self, event):
        """
        Send version saved notification to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'version_saved',
            'user_id': event['user_id'],
            'username': event['username'],
            'version_number': event['version_number'],
            'comment': event['comment'],
            'timestamp': event['timestamp']
        }))

    async def chat_message(self, event):
        """
        Send chat message to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'user_id': event['user_id'],
            'username': event['username'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))

    async def user_joined(self, event):
        """
        Send user joined notification to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def user_left(self, event):
        """
        Send user left notification to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    # Database access methods
    @database_sync_to_async
    def has_content_access(self):
        """
        Check if the user has access to this content
        """
        try:
            content = Content.objects.get(id=self.content_id)
            # Check if user is author or has edit permission
            # This is a simple check, you might want to implement more sophisticated permission logic
            return self.user.is_authenticated and (content.author == self.user or self.user.is_staff)
        except Content.DoesNotExist:
            return False

    @database_sync_to_async
    def save_content_version(self, content_data, comment):
        """
        Save a new version of the content
        """
        content = Content.objects.get(id=self.content_id)
        
        # Update the content
        content.content = content_data
        content.updated_at = timezone.now()
        content.save()
        
        # Create a new version
        latest_version = ContentVersion.objects.filter(content=content).order_by('-version_number').first()
        new_version_number = 1 if not latest_version else latest_version.version_number + 1
        
        version = ContentVersion.objects.create(
            content=content,
            version_number=new_version_number,
            content_data=content_data,
            created_by=self.user,
            comment=comment
        )
        
        return version