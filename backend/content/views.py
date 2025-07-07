from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import Post, Comment, Like, PostMedia, Share, UserInteraction
from .serializers import PostSerializer, CommentCreateSerializer, CommentSerializer, ShareSerializer, UserInteractionCreateSerializer
from django.db.models import Q
from .feed_algorithm import FeedAlgorithm

API_VERSION = "1.0"

def api_response(success, data=None, message="", errors=None, status_code=200):
    return Response({
        "success": success,
        "data": data,
        "message": message,
        "errors": errors,
        "meta": {
            "timestamp": timezone.now().isoformat(),
            "version": API_VERSION,
        }
    }, status=status_code)

class PostFeedView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Base queryset for filtering
        # This should be as broad as possible, letting the algorithm do the ranking.
        user_profile = user.profile
        user_courses = user.enrolled_courses.all()

        # Fetch posts relevant to the user's context (campus, courses, public)
        return Post.objects.filter(
            Q(visibility='public') |
            Q(location=user_profile.campus) |
            Q(course__in=user_courses)
        ).distinct().select_related('author', 'course', 'location').prefetch_related('likes', 'comments', 'shares')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user = request.user

        # Rank the feed using the algorithm
        feed_algorithm = FeedAlgorithm(user)
        ranked_feed = feed_algorithm.rank_feed(queryset)

        # Pagination
        try:
            page = int(request.query_params.get('page', 1))
            limit = int(request.query_params.get('limit', 20))
        except ValueError:
            page = 1
            limit = 20

        if limit > 50:
            limit = 50

        start = (page - 1) * limit
        end = start + limit
        paginated_feed = ranked_feed[start:end]

        # Log post views for the paginated items
        if paginated_feed:
            interactions_to_create = [
                UserInteraction(user=user, post=post, interaction_type='view') for post in paginated_feed
            ]
            UserInteraction.objects.bulk_create(interactions_to_create, ignore_conflicts=True)

        # Serialize the data
        serializer = self.get_serializer(paginated_feed, many=True, context={'request': request})

        return api_response(
            True,
            {
                'posts': serializer.data,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': len(ranked_feed),
                    'has_next': end < len(ranked_feed)
                }
            },
            "Feed retrieved successfully"
        )


class UserInteractionCreateView(generics.CreateAPIView):
    """
    Logs user interactions with posts, such as views, likes, shares, etc.
    This data is crucial for the feed algorithm to learn user preferences.
    """
    serializer_class = UserInteractionCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Ensure the user is not duplicated for the same interaction
            interaction_type = serializer.validated_data.get('interaction_type')
            post = serializer.validated_data.get('post')
            
            if interaction_type != 'view': # Views can be logged multiple times
                _, created = UserInteraction.objects.get_or_create(
                    user=request.user,
                    post=post,
                    interaction_type=interaction_type,
                    defaults=serializer.validated_data
                )
                if not created:
                    return api_response(
                        False,
                        None,
                        f"You have already interacted with this post with type '{interaction_type}'.",
                        status_code=status.HTTP_409_CONFLICT
                    )
            else:
                 serializer.save()

            return api_response(
                True,
                serializer.data,
                "Interaction logged successfully.",
                status_code=status.HTTP_201_CREATED
            )
        return api_response(
            False,
            None,
            "Interaction logging failed.",
            serializer.errors,
            status.HTTP_400_BAD_REQUEST
        )


class PostCreateView(generics.CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            post = serializer.save()

            # Handle media files
            media_files = request.FILES.getlist('media')
            for i, file in enumerate(media_files):
                PostMedia.objects.create(
                    post=post,
                    media_type=file.content_type.split('/')[0],
                    file=file,
                    order=i
                )
            
            # Re-serialize the post to include media
            serializer = self.get_serializer(post)
            return api_response(
                True,
                serializer.data,
                "Post created successfully",
                status_code=201
            )
        return api_response(
            False,
            None,
            "Post creation failed",
            serializer.errors,
            400
        )


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, serializer.data, "Post retrieved successfully")

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return api_response(False, None, "You do not have permission to edit this post.", status_code=403)
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, serializer.data, "Post updated successfully")
        return api_response(False, None, "Post update failed", serializer.errors, 400)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return api_response(False, None, "You do not have permission to delete this post.", status_code=403)
        
        instance.delete()
        return api_response(True, None, "Post deleted successfully", status_code=204)


class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return api_response(True, serializer.data, "Comment created successfully", status_code=201)
        return api_response(False, None, "Comment creation failed", serializer.errors, 400)


class CommentListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id, parent_comment__isnull=True).order_by('created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, serializer.data, "Comments retrieved successfully")


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # A user can only modify/delete their own comments
        return Comment.objects.filter(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, serializer.data, "Comment retrieved successfully")

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Redundant check as get_queryset already filters, but good for safety
        if instance.author != request.user:
            return api_response(False, None, "You do not have permission to edit this comment.", status_code=403)
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, serializer.data, "Comment updated successfully")
        return api_response(False, None, "Comment update failed", serializer.errors, 400)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Redundant check as get_queryset already filters, but good for safety
        if instance.author != request.user:
            return api_response(False, None, "You do not have permission to delete this comment.", status_code=403)
        
        instance.delete()
        return api_response(True, None, "Comment deleted successfully", status_code=204)


class ShareCreateView(generics.CreateAPIView):
    serializer_class = ShareSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        
        if Share.objects.filter(user=request.user, post=post).exists():
            return api_response(False, None, "You have already shared this post.", status_code=400)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, post=post)
            return api_response(True, serializer.data, "Post shared successfully", status_code=201)
        return api_response(False, None, "Share creation failed", serializer.errors, 400)


class LikeToggleView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        user = request.user

        like, created = Like.objects.get_or_create(user=user, post=post)

        if created:
            return api_response(True, None, "Post liked successfully", status_code=201)
        else:
            like.delete()
            return api_response(True, None, "Post unliked successfully", status_code=204)
