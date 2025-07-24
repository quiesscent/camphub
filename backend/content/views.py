from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import OpenApiResponse
from drf_spectacular.types import OpenApiTypes
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

    @extend_schema(
        description="Get personalized content feed based on user preferences, interactions, and machine learning algorithms",
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Page number for pagination (default: 1)',
                required=False
            ),
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of posts per page (max: 50, default: 20)',
                required=False
            ),
            OpenApiParameter(
                name='content_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by post type: text, image, video, document, event, marketplace',
                required=False
            ),
            OpenApiParameter(
                name='visibility',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by visibility: public, friends, course, anonymous',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Personalized feed retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "data": {
                                "posts": [
                                    {
                                        "id": 1,
                                        "author": {
                                            "id": 2,
                                            "first_name": "Jane",
                                            "last_name": "Doe",
                                            "profile_picture": "/media/profile_pictures/jane.jpg"
                                        },
                                        "content": "Excited about the upcoming CS lecture!",
                                        "post_type": "text",
                                        "visibility": "public",
                                        "course": "Computer Science 101",
                                        "location": "Main Campus",
                                        "likes_count": 15,
                                        "comments_count": 3,
                                        "is_liked": False,
                                        "media": [],
                                        "created_at": "2024-01-01T10:00:00Z"
                                    }
                                ],
                                "pagination": {
                                    "page": 1,
                                    "limit": 20,
                                    "total": 45,
                                    "has_next": True
                                }
                            },
                            "message": "Feed retrieved successfully"
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Content Feed']
    )
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

    @extend_schema(
        description="Log user interactions with posts for feed algorithm learning and analytics",
        request=UserInteractionCreateSerializer,
        responses={
            201: OpenApiResponse(
                description="Interaction logged successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "data": {
                                "id": 123,
                                "post": 1,
                                "interaction_type": "like",
                                "duration_seconds": 5.2,
                                "timestamp": "2024-01-01T10:30:00Z"
                            },
                            "message": "Interaction logged successfully"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Validation error",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        value={
                            "success": False,
                            "errors": {
                                "post": ["This field is required"],
                                "interaction_type": ["Invalid interaction type"]
                            },
                            "message": "Interaction logging failed"
                        }
                    )
                ]
            ),
            409: OpenApiResponse(
                description="Duplicate interaction",
                examples=[
                    OpenApiExample(
                        "Duplicate",
                        value={
                            "success": False,
                            "message": "You have already interacted with this post with type 'like'"
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Content Interactions'],
        examples=[
            OpenApiExample(
                "Like Interaction",
                value={
                    "post": 1,
                    "interaction_type": "like",
                    "duration_seconds": 2.5
                }
            ),
            OpenApiExample(
                "View Interaction",
                value={
                    "post": 1,
                    "interaction_type": "view",
                    "duration_seconds": 15.7
                }
            )
        ]
    )
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

    @extend_schema(
        description="Create a new post with optional media attachments",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'content': {
                        'type': 'string',
                        'description': 'Post content/text'
                    },
                    'post_type': {
                        'type': 'string',
                        'enum': ['text', 'image', 'video', 'document', 'event', 'marketplace'],
                        'description': 'Type of post content'
                    },
                    'visibility': {
                        'type': 'string',
                        'enum': ['public', 'friends', 'course', 'anonymous'],
                        'description': 'Post visibility level'
                    },
                    'course_id': {
                        'type': 'integer',
                        'description': 'ID of course to associate with post (optional)'
                    },
                    'location_id': {
                        'type': 'integer',
                        'description': 'ID of campus location (optional)'
                    },
                    'is_anonymous': {
                        'type': 'boolean',
                        'description': 'Whether to post anonymously'
                    },
                    'tags': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Tags for categorizing the post'
                    },
                    'media': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                            'format': 'binary'
                        },
                        'description': 'Media files (images, videos, documents - max 10MB each)'
                    }
                }
            }
        },
        responses={
            201: OpenApiResponse(
                description="Post created successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "data": {
                                "id": 1,
                                "author": {
                                    "id": 1,
                                    "first_name": "John",
                                    "last_name": "Doe"
                                },
                                "content": "Just finished my CS assignment!",
                                "post_type": "text",
                                "visibility": "public",
                                "course": "Computer Science 101",
                                "media": [
                                    {
                                        "id": 1,
                                        "media_type": "image",
                                        "file": "/media/post_media/assignment.jpg",
                                        "caption": "My completed assignment"
                                    }
                                ],
                                "likes_count": 0,
                                "comments_count": 0,
                                "is_liked": False,
                                "created_at": "2024-01-01T10:00:00Z"
                            },
                            "message": "Post created successfully"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Posts']
    )
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

    @extend_schema(
        description="Get detailed information about a specific post including media and interaction counts",
        responses={
            200: OpenApiResponse(
                description="Post retrieved successfully",
                response=PostSerializer
            ),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Post not found")
        },
        tags=['Posts']
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, serializer.data, "Post retrieved successfully")

    @extend_schema(
        description="Update a post (only author can update)",
        request=PostSerializer,
        responses={
            200: OpenApiResponse(
                description="Post updated successfully",
                response=PostSerializer
            ),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not post author"),
            404: OpenApiResponse(description="Post not found")
        },
        tags=['Posts']
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return api_response(False, None, "You do not have permission to edit this post.", status_code=403)
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, serializer.data, "Post updated successfully")
        return api_response(False, None, "Post update failed", serializer.errors, 400)

    @extend_schema(
        description="Delete a post (only author can delete)",
        responses={
            204: OpenApiResponse(description="Post deleted successfully"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not post author"),
            404: OpenApiResponse(description="Post not found")
        },
        tags=['Posts']
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return api_response(False, None, "You do not have permission to delete this post.", status_code=403)
        
        instance.delete()
        return api_response(True, None, "Post deleted successfully", status_code=204)


class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Create a comment on a post or reply to another comment",
        request=CommentCreateSerializer,
        responses={
            201: OpenApiResponse(
                description="Comment created successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "data": {
                                "id": 1,
                                "post": 1,
                                "author": {
                                    "id": 1,
                                    "first_name": "John",
                                    "last_name": "Doe"
                                },
                                "content": "Great post! Thanks for sharing.",
                                "parent_comment": None,
                                "is_anonymous": False,
                                "created_at": "2024-01-01T10:30:00Z"
                            },
                            "message": "Comment created successfully"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Comments'],
        examples=[
            OpenApiExample(
                "Top-level Comment",
                value={
                    "post": 1,
                    "content": "Great post! Very informative.",
                    "is_anonymous": False
                }
            ),
            OpenApiExample(
                "Reply Comment",
                value={
                    "post": 1,
                    "content": "I agree with your point!",
                    "parent_comment": 1,
                    "is_anonymous": False
                }
            )
        ]
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return api_response(True, serializer.data, "Comment created successfully", status_code=201)
        return api_response(False, None, "Comment creation failed", serializer.errors, 400)


class CommentListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Get all top-level comments for a specific post with nested replies",
        parameters=[
            OpenApiParameter(
                name='post_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID of the post to get comments for'
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Comments retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "data": [
                                {
                                    "id": 1,
                                    "author": {
                                        "id": 2,
                                        "first_name": "Jane",
                                        "last_name": "Smith"
                                    },
                                    "content": "This is really helpful!",
                                    "parent_comment": None,
                                    "is_anonymous": False,
                                    "created_at": "2024-01-01T10:30:00Z",
                                    "replies": [
                                        {
                                            "id": 2,
                                            "author": {
                                                "id": 1,
                                                "first_name": "John",
                                                "last_name": "Doe"
                                            },
                                            "content": "Glad you found it useful!",
                                            "parent_comment": 1,
                                            "is_anonymous": False,
                                            "created_at": "2024-01-01T10:35:00Z",
                                            "replies": []
                                        }
                                    ]
                                }
                            ],
                            "message": "Comments retrieved successfully"
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Post not found")
        },
        tags=['Comments']
    )
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

    @extend_schema(
        description="Get, update, or delete a specific comment (only comment author can modify)",
        responses={
            200: OpenApiResponse(
                description="Comment retrieved/updated successfully",
                response=CommentSerializer
            ),
            204: OpenApiResponse(description="Comment deleted successfully"),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not comment author"),
            404: OpenApiResponse(description="Comment not found")
        },
        tags=['Comments']
    )
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

    @extend_schema(
        description="Share a post with optional caption (one share per user per post)",
        parameters=[
            OpenApiParameter(
                name='post_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID of the post to share'
            )
        ],
        request=ShareSerializer,
        responses={
            201: OpenApiResponse(
                description="Post shared successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "data": {
                                "id": 1,
                                "user": {
                                    "id": 1,
                                    "first_name": "John",
                                    "last_name": "Doe"
                                },
                                "post": 1,
                                "caption": "This is really worth sharing!",
                                "created_at": "2024-01-01T10:45:00Z"
                            },
                            "message": "Post shared successfully"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Already shared or validation error",
                examples=[
                    OpenApiExample(
                        "Already Shared",
                        value={
                            "success": False,
                            "message": "You have already shared this post"
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Post not found")
        },
        tags=['Post Interactions'],
        examples=[
            OpenApiExample(
                "Share with Caption",
                value={
                    "caption": "This is exactly what I was looking for!"
                }
            ),
            OpenApiExample(
                "Share without Caption",
                value={
                    "caption": ""
                }
            )
        ]
    )
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

    @extend_schema(
        description="Toggle like status on a post (like if not liked, unlike if already liked)",
        parameters=[
            OpenApiParameter(
                name='post_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID of the post to like/unlike'
            )
        ],
        request=None,
        responses={
            201: OpenApiResponse(
                description="Post liked successfully",
                examples=[
                    OpenApiExample(
                        "Liked",
                        value={
                            "success": True,
                            "message": "Post liked successfully"
                        }
                    )
                ]
            ),
            204: OpenApiResponse(
                description="Post unliked successfully",
                examples=[
                    OpenApiExample(
                        "Unliked",
                        value={
                            "success": True,
                            "message": "Post unliked successfully"
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Post not found")
        },
        tags=['Post Interactions']
    )
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
