from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class PageView(models.Model):
    """
    Tracks page views for any content
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Visitor information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='page_views')
    session_id = models.CharField(_("Session ID"), max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(_("IP Address"), blank=True, null=True)
    user_agent = models.TextField(_("User Agent"), blank=True)
    referrer = models.URLField(_("Referrer"), blank=True)
    
    # Content metadata at the time of viewing
    content_title = models.CharField(_("Content Title"), max_length=255, blank=True)
    
    # Timestamp
    viewed_at = models.DateTimeField(_("Viewed At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Page View")
        verbose_name_plural = _("Page Views")
        ordering = ["-viewed_at"]
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"View of {self.content_object} at {self.viewed_at}"

class UserActivity(models.Model):
    """
    Tracks user activity across the platform
    """
    ACTIVITY_TYPES = (
        ('content_created', _('Content Created')),
        ('content_edited', _('Content Edited')),
        ('content_published', _('Content Published')),
        ('content_archived', _('Content Archived')),
        ('content_commented', _('Content Commented')),
        ('ai_request', _('AI Request')),
        ('login', _('Login')),
        ('other', _('Other')),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(_("Activity Type"), max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField(_("Description"), blank=True)
    
    # Related content (optional)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='user_activities')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional data (as JSON)
    extra_data = models.JSONField(_("Extra Data"), default=dict, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("User Activity")
        verbose_name_plural = _("User Activities")
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.created_at}"

class ContentPerformanceMetric(models.Model):
    """
    Aggregated performance metrics for content
    """
    PERIOD_CHOICES = (
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly')),
        ('all_time', _('All Time')),
    )
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Time period
    period_type = models.CharField(_("Period Type"), max_length=20, choices=PERIOD_CHOICES)
    period_start = models.DateField(_("Period Start"), null=True, blank=True)
    period_end = models.DateField(_("Period End"), null=True, blank=True)
    
    # Metrics
    view_count = models.PositiveIntegerField(_("View Count"), default=0)
    unique_view_count = models.PositiveIntegerField(_("Unique View Count"), default=0)
    average_time_spent_seconds = models.PositiveIntegerField(_("Average Time Spent (seconds)"), default=0)
    bounce_rate = models.FloatField(_("Bounce Rate"), default=0)
    conversion_count = models.PositiveIntegerField(_("Conversion Count"), default=0)
    
    # Metadata
    last_updated = models.DateTimeField(_("Last Updated"), auto_now=True)
    
    class Meta:
        verbose_name = _("Content Performance Metric")
        verbose_name_plural = _("Content Performance Metrics")
        ordering = ["-period_start"]
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'period_type']),
        ]
        unique_together = ['content_type', 'object_id', 'period_type', 'period_start']
    
    def __str__(self):
        period_info = f" - {self.period_type}"
        if self.period_start:
            period_info += f" ({self.period_start})"
        return f"Metrics for {self.content_object}{period_info}"