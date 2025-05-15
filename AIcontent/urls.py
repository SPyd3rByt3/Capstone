from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContentViewSet, ContentCategoryViewSet, TagViewSet, ContentCommentViewSet

router = DefaultRouter()
router.register(r'contents', ContentViewSet, basename='content')
router.register(r'categories', ContentCategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'comments', ContentCommentViewSet, basename='comment')

urlpatterns = [
    path('', include(router.urls)),
]
