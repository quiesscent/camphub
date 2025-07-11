from django.urls import path
from content.views import (
    PostFeedView,
    PostCreateView,
    PostDetailView,
    CommentCreateView,
    CommentListView,
    LikeToggleView,
    CommentDetailView,
    ShareCreateView
)

urlpatterns = [
    path('feed/', PostFeedView.as_view(), name='post-feed'),
    path('', PostCreateView.as_view(), name='post-create'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('<int:post_id>/comments/', CommentListView.as_view(), name='comment-list'),
    path('comments/', CommentCreateView.as_view(), name='comment-create'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
    path('<int:post_id>/like/', LikeToggleView.as_view(), name='like-toggle'),
    path('<int:post_id>/share/', ShareCreateView.as_view(), name='share-create'),
]
