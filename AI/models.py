# from django.db import models

# # Create your models here.
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class AIModel(models.Model):
    """
    Represents different AI models that can be used for generation
    """
    MODEL_PROVIDERS = (
        ('openai', _('OpenAI')),
        ('anthropic', _('Anthropic')),
        ('internal', _('Internal')),
        ('other', _('Other')),
    )
    
    name = models.CharField(_("Model Name"), max_length=100)
    provider = models.CharField(_("Provider"), max_length=20, choices=MODEL_PROVIDERS)
    model_identifier = models.CharField(_("Model Identifier"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    # Configuration
    default_temperature = models.FloatField(_("Default Temperature"), default=0.7)
    default_max_tokens = models.PositiveIntegerField(_("Default Max Tokens"), default=1000)
    
    class Meta:
        verbose_name = _("AI Model")
        verbose_name_plural = _("AI Models")
        ordering = ["name"]
    
    def __str__(self):
        return f"{self.name} ({self.provider})"

class PromptTemplate(models.Model):
    """
    Reusable prompt templates for AI content generation
    """
    name = models.CharField(_("Template Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    prompt_text = models.TextField(_("Prompt Text"))
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='prompt_templates')
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    is_public = models.BooleanField(_("Is Public"), default=False)
    
    class Meta:
        verbose_name = _("Prompt Template")
        verbose_name_plural = _("Prompt Templates")
        ordering = ["-created_at"]
    
    def __str__(self):
        return self.name

class AIContentRequest(models.Model):
    """
    Record of AI content generation requests
    """
    REQUEST_TYPES = (
        ('generation', _('Content Generation')),
        ('enhancement', _('Content Enhancement')),
        ('editing', _('Content Editing')),
        ('summarization', _('Summarization')),
        ('translation', _('Translation')),
        ('other', _('Other')),
    )
    
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_requests')
    request_type = models.CharField(_("Request Type"), max_length=20, choices=REQUEST_TYPES)
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, related_name='requests')
    prompt = models.TextField(_("Prompt"))
    prompt_template = models.ForeignKey(PromptTemplate, on_delete=models.SET_NULL, 
                                        null=True, blank=True, related_name='ai_requests')
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Configuration used
    temperature = models.FloatField(_("Temperature"), default=0.7)
    max_tokens = models.PositiveIntegerField(_("Max Tokens"), default=1000)
    
    # Response data
    response_text = models.TextField(_("Response Text"), blank=True)
    error_message = models.TextField(_("Error Message"), blank=True)
    
    # Target content (optional)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, 
                                     null=True, blank=True, related_name='ai_requests')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target_object = GenericForeignKey('content_type', 'object_id')
    
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)
    
    # Metrics
    token_count_input = models.PositiveIntegerField(_("Input Token Count"), default=0)
    token_count_output = models.PositiveIntegerField(_("Output Token Count"), default=0)
    processing_time_ms = models.PositiveIntegerField(_("Processing Time (ms)"), default=0)
    
    class Meta:
        verbose_name = _("AI Content Request")
        verbose_name_plural = _("AI Content Requests")
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.request_type} by {self.user.username} - {self.status}"

class AIContentFeedback(models.Model):
    """
    User feedback on AI-generated content to improve AI performance
    """
    RATING_CHOICES = (
        (1, _('Poor')),
        (2, _('Fair')),
        (3, _('Good')),
        (4, _('Very Good')),
        (5, _('Excellent')),
    )
    
    ai_request = models.ForeignKey(AIContentRequest, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_feedback')
    rating = models.PositiveSmallIntegerField(_("Rating"), choices=RATING_CHOICES)
    comment = models.TextField(_("Comment"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("AI Content Feedback")
        verbose_name_plural = _("AI Content Feedback")
        ordering = ["-created_at"]
        unique_together = ['ai_request', 'user']
    
    def __str__(self):
        return f"Feedback by {self.user.username} - Rating: {self.rating}"