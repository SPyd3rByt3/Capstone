from rest_framework import serializers
from .models import Content, ContentCategory, Tag, ContentCollaborator, ContentVersion, ContentComment
from django.contrib.auth import get_user_model

User = get_user_model()

class ContentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentCategory
        fields = ['id', 'name', 'slug', 'description', 'parent']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']

class ContentCollaboratorSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = ContentCollaborator
        fields = ['id', 'user', 'role', 'joined_at']

class ContentVersionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = ContentVersion
        fields = ['id', 'version_number', 'content_body', 'content_json', 'created_by', 'created_at', 'comment']

class ContentCommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = ContentComment
        fields = ['id', 'content', 'author', 'text', 'created_at', 'updated_at', 'parent', 'replies', 'selection_start', 'selection_end', 'selected_text']

    def get_replies(self, obj):
        if obj.replies:
            return ContentCommentSerializer(obj.replies.all(), many=True).data
        return []

class ContentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    category = ContentCategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    collaborators = ContentCollaboratorSerializer(source='contentcollaborator_set', many=True, read_only=True)
    versions = ContentVersionSerializer(many=True, read_only=True)
    comments = ContentCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Content
        fields = [
            'id', 'title', 'slug', 'author', 'category', 'tags', 'description', 'featured_image',
            'content_body', 'content_json', 'ai_generated', 'ai_prompted', 'ai_prompt', 'status',
            'visibility', 'created_at', 'updated_at', 'published_at', 'collaborators', 'view_count',
            'engagement_score', 'versions', 'comments'
        ]
