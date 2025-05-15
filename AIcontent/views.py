from rest_framework import viewsets, permissions
from .models import Content, ContentCategory, Tag, ContentComment
from .serializers import ContentSerializer, ContentCategorySerializer, TagSerializer, ContentCommentSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, pk=None):
        content = self.get_object()
        content.publish()
        return Response({'status': 'content published'})

class ContentCategoryViewSet(viewsets.ModelViewSet):
    queryset = ContentCategory.objects.all()
    serializer_class = ContentCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ContentCommentViewSet(viewsets.ModelViewSet):
    queryset = ContentComment.objects.all()
    serializer_class = ContentCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
