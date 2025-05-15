# from django.db import models

# # Create your models here.
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()


class ContentCategory(models.Model):
    """
    Categories for organizing content.
    """
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True)
    description = models.TextField(_('description'), blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='children'
    )
    
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    """
    Tags for content items.
    """
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True)
    
    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Content(models.Model):
    """
    Base content model for all types of content.
    """
    title = models.CharField(_('title'), max_length=255)
    slug = models.SlugField(_('slug'), unique=True)
    
    # Content details
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='content'
    )
    category = models.ForeignKey(
        ContentCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='content_items'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='content_items')
    
    # Content metadata
    description = models.TextField(_('description'), blank=True)
    featured_image = models.ImageField(
        upload_to='content_images/', 
        blank=True, 
        null=True
    )
    
    # Actual content data
    content_body = models.TextField(_('content body'))
    content_json = models.JSONField(_('content JSON'), default=dict, blank=True)
    
    # AI assistance info
    ai_generated = models.BooleanField(_('AI generated'), default=False)
    ai_prompted = models.BooleanField(_('AI prompted'), default=False)
    ai_prompt = models.TextField(_('AI prompt'), blank=True)
    
    # Publishing status
    class PublishStatus(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        REVIEW = 'REVIEW', _('In Review')
        PUBLISHED = 'PUBLISHED', _('Published')
        ARCHIVED = 'ARCHIVED', _('Archived')
    
    status = models.CharField(
        max_length=10,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
    )
    
    # Visibility and access
    class VisibilityType(models.TextChoices):
        PUBLIC = 'PUBLIC', _('Public')
        PRIVATE = 'PRIVATE', _('Private')
        SHARED = 'SHARED', _('Shared')
    
    visibility = models.CharField(
        max_length=10,
        choices=VisibilityType.choices,
        default=VisibilityType.PRIVATE,
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    published_at = models.DateTimeField(_('published at'), null=True, blank=True)
    
    # Collaborators
    collaborators = models.ManyToManyField(
        User, 
        through='ContentCollaborator',
        related_name='collaborative_content'
    )
    
    # Analytics data
    view_count = models.PositiveIntegerField(_('view count'), default=0)
    engagement_score = models.FloatField(_('engagement score'), default=0.0)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('content')
        verbose_name_plural = _('content')
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Set published_at when status changes to PUBLISHED
        if self.status == self.PublishStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('content:detail', kwargs={'slug': self.slug})
    
    def publish(self):
        """Publish this content."""
        self.status = self.PublishStatus.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at'])
    
    def increment_view_count(self):
        """Increment the view count for this content."""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def update_engagement_score(self, new_score):
        """Update the engagement score."""
        # Simple average calculation
        self.engagement_score = (self.engagement_score + new_score) / 2
        self.save(update_fields=['engagement_score'])


class ContentCollaborator(models.Model):
    """
    Through model for Content-User many-to-many relationship.
    """
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Role(models.TextChoices):
        EDITOR = 'EDITOR', _('Editor')
        REVIEWER = 'REVIEWER', _('Reviewer')
        VIEWER = 'VIEWER', _('Viewer')
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.VIEWER,
    )
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('content', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.content.title} ({self.get_role_display()})"


class ContentVersion(models.Model):
    """
    Version history for content.
    """
    content = models.ForeignKey(
        Content, 
        on_delete=models.CASCADE, 
        related_name='versions'
    )
    version_number = models.PositiveIntegerField()
    content_body = models.TextField()
    content_json = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('content', 'version_number')
        ordering = ['-version_number']
    
    def __str__(self):
        return f"{self.content.title} - v{self.version_number}"


class ContentComment(models.Model):
    """
    Comments on content.
    """
    content = models.ForeignKey(
        Content, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For threaded comments
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies'
    )
    
    # For annotating specific parts of content
    selection_start = models.PositiveIntegerField(null=True, blank=True)
    selection_end = models.PositiveIntegerField(null=True, blank=True)
    selected_text = models.TextField(blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.content.title}"