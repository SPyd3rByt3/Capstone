from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from AIcontent.models import Content

User = settings.AUTH_USER_MODEL


class CollaborationSession(models.Model):
    """
    Represents a real-time collaboration session on a piece of content.
    """
    content = models.ForeignKey(
        'AIcontent.Content',  # Using AIcontent instead of content
        on_delete=models.CASCADE,
        related_name='collaboration_sessions'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_sessions'
    )
    
    # Session metadata
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    
    # Session status
    class SessionStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        PAUSED = 'PAUSED', _('Paused')
        COMPLETED = 'COMPLETED', _('Completed')
    
    status = models.CharField(
        max_length=10,
        choices=SessionStatus.choices,
        default=SessionStatus.ACTIVE
    )
    
    # Session participants tracking
    participants = models.ManyToManyField(
        User,
        through='SessionParticipant',
        related_name='participating_sessions'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Session settings
    max_participants = models.PositiveIntegerField(default=10)
    is_public = models.BooleanField(default=False)
    join_code = models.CharField(max_length=20, blank=True, null=True, unique=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('collaboration session')
        verbose_name_plural = _('collaboration sessions')
    
    def __str__(self):
        return f"Session on {self.content.title}"
    
    def complete(self):
        """Mark the session as completed."""
        self.status = self.SessionStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def is_active(self):
        """Check if the session is active."""
        return self.status == self.SessionStatus.ACTIVE
    
    def can_join(self, user):
        """Check if a user can join this session."""
        if not self.is_active():
            return False
        
        # Check if max participants reached
        if self.participants.count() >= self.max_participants:
            return False
        
        # Check if user has permission to edit the content
        # This depends on your specific permission logic
        return True
    
    def add_participant(self, user, role='VIEWER'):
        """Add a participant to the session."""
        if not self.can_join(user):
            return False
        
        participant, created = SessionParticipant.objects.get_or_create(
            session=self,
            user=user,
            defaults={'role': role}
        )
        
        return participant


class SessionParticipant(models.Model):
    """
    Through model for tracking participants in a collaboration session.
    """
    session = models.ForeignKey(CollaborationSession, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Participant role in the session
    class ParticipantRole(models.TextChoices):
        LEADER = 'LEADER', _('Session Leader')
        EDITOR = 'EDITOR', _('Editor')
        VIEWER = 'VIEWER', _('Viewer')
    
    role = models.CharField(
        max_length=10,
        choices=ParticipantRole.choices,
        default=ParticipantRole.VIEWER
    )
    
    # Status tracking
    joined_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    is_present = models.BooleanField(default=True)
    
    # Cursor position tracking
    cursor_position = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ['session', 'user']
        verbose_name = _('session participant')
        verbose_name_plural = _('session participants')
    
    def __str__(self):
        return f"{self.user.username} in {self.session}"
    
    def update_cursor(self, position_data):
        """Update cursor position for this participant."""
        self.cursor_position = position_data
        self.last_active = timezone.now()
        self.save(update_fields=['cursor_position', 'last_active'])
    
    def set_presence(self, is_present):
        """Update the presence status of this participant."""
        self.is_present = is_present
        self.save(update_fields=['is_present', 'last_active'])


class CollaborationAction(models.Model):
    """
    Records actions performed during a collaboration session.
    """
    session = models.ForeignKey(
        CollaborationSession,
        on_delete=models.CASCADE,
        related_name='actions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='collaboration_actions'
    )
    
    # Action type
    class ActionType(models.TextChoices):
        EDIT = 'EDIT', _('Edit Content')
        COMMENT = 'COMMENT', _('Add Comment')
        FORMAT = 'FORMAT', _('Format Content')
        SUGGEST = 'SUGGEST', _('Suggest Edit')
        APPROVE = 'APPROVE', _('Approve Edit')
        REJECT = 'REJECT', _('Reject Edit')
        OTHER = 'OTHER', _('Other Action')
    
    action_type = models.CharField(
        max_length=10,
        choices=ActionType.choices,
        default=ActionType.EDIT
    )
    
    # Action data
    content_before = models.TextField(blank=True)
    content_after = models.TextField(blank=True)
    action_data = models.JSONField(default=dict)
    
    # Position information
    position_start = models.PositiveIntegerField(default=0)
    position_end = models.PositiveIntegerField(default=0)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = _('collaboration action')
        verbose_name_plural = _('collaboration actions')
    
    def __str__(self):
        return f"{self.action_type} by {self.user.username}"


class Comment(models.Model):
    """
    Comments made during collaboration sessions.
    """
    session = models.ForeignKey(
        CollaborationSession,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='collaboration_comments'
    )
    
    # Comment content
    text = models.TextField()
    position = models.JSONField(default=dict)  # For positioning the comment in the document
    
    # Comment status
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_comments'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
    
    def __str__(self):
        return f"Comment by {self.user.username}"
    
    def resolve(self, user):
        """Mark the comment as resolved."""
        self.is_resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save(update_fields=['is_resolved', 'resolved_by', 'resolved_at'])