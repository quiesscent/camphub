from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Post, PostMedia, Comment, Like, Share, UserInteraction
from users.serializers import UserSerializer
from users.models import Campus
from academic.models import Course

User = get_user_model()


class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = ['id', 'media_type', 'file', 'caption', 'order']
        
    media_type = serializers.CharField(
        read_only=True,
        help_text="Type of media file: image, video, or document"
    )
    file = serializers.FileField(
        read_only=True,
        help_text="URL to the uploaded media file"
    )
    caption = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Optional caption or description for the media",
        error_messages={
            'max_length': 'Caption cannot exceed 255 characters'
        }
    )
    order = serializers.IntegerField(
        read_only=True,
        help_text="Display order of media within the post"
    )


class RecursiveCommentSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = RecursiveCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'parent_comment', 'is_anonymous', 'created_at', 'replies']
        
    content = serializers.CharField(
        help_text="Comment content text",
        error_messages={
            'required': 'Comment content is required',
            'blank': 'Comment cannot be empty'
        }
    )
    parent_comment = serializers.PrimaryKeyRelatedField(
        read_only=True,
        help_text="ID of parent comment if this is a reply, null for top-level comments"
    )
    is_anonymous = serializers.BooleanField(
        read_only=True,
        help_text="Whether the comment was posted anonymously"
    )
    created_at = serializers.DateTimeField(
        read_only=True,
        help_text="Timestamp when the comment was created"
    )


class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'created_at']
        
    created_at = serializers.DateTimeField(
        read_only=True,
        help_text="Timestamp when the like was created"
    )


class ShareSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Share
        fields = ['id', 'user', 'post', 'caption', 'created_at']
        
    caption = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Optional caption when sharing the post",
        error_messages={
            'max_length': 'Share caption cannot exceed 500 characters'
        }
    )
    created_at = serializers.DateTimeField(
        read_only=True,
        help_text="Timestamp when the post was shared"
    )


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    media = PostMediaSerializer(many=True, read_only=True)
    course = serializers.StringRelatedField()
    location = serializers.StringRelatedField()
    
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source='course',
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID of course to associate with this post (optional)",
        error_messages={
            'does_not_exist': 'Course with this ID does not exist'
        }
    )
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Campus.objects.all(),
        source='location',
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID of campus location for this post (optional)",
        error_messages={
            'does_not_exist': 'Campus location with this ID does not exist'
        }
    )

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content', 'post_type', 'visibility', 
            'course', 'location', 'is_pinned', 'is_anonymous', 
            'created_at', 'updated_at', 'media', 'tags',
            'likes_count', 'comments_count', 'is_liked',
            'course_id', 'location_id'
        ]
        read_only_fields = ('author', 'created_at', 'updated_at', 'media', 'is_pinned')
        
    content = serializers.CharField(
        help_text="Main content/text of the post",
        error_messages={
            'required': 'Post content is required',
            'blank': 'Post content cannot be empty'
        }
    )
    post_type = serializers.ChoiceField(
        choices=Post.POST_TYPE_CHOICES,
        default='text',
        help_text="Type of post: text, image, video, document, event, marketplace",
        error_messages={
            'invalid_choice': 'Post type must be one of: text, image, video, document, event, marketplace'
        }
    )
    visibility = serializers.ChoiceField(
        choices=Post.VISIBILITY_CHOICES,
        default='public',
        help_text="Visibility level: public, friends, course, anonymous",
        error_messages={
            'invalid_choice': 'Visibility must be one of: public, friends, course, anonymous'
        }
    )
    is_anonymous = serializers.BooleanField(
        default=False,
        help_text="Whether to post anonymously (hides author information)"
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
        help_text="List of tags for categorizing the post",
        error_messages={
            'invalid': 'Tags must be a list of strings'
        }
    )

    def get_likes_count(self, obj):
        """Get total number of likes for this post"""
        return obj.likes.count()

    def get_comments_count(self, obj):
        """Get total number of comments for this post"""
        return obj.comments.count()

    def get_is_liked(self, obj):
        """Check if current user has liked this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(post=obj, user=request.user).exists()
        return False

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return Post.objects.create(**validated_data)


class UserInteractionCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserInteraction
        fields = ['id', 'user', 'post', 'interaction_type', 'dwell_time']
        
    post = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(),
        help_text="ID of the post being interacted with",
        error_messages={
            'required': 'Post ID is required',
            'does_not_exist': 'Post with this ID does not exist'
        }
    )
    interaction_type = serializers.ChoiceField(
        choices=UserInteraction._meta.get_field('interaction_type').choices,
        help_text="Type of interaction: view, like, comment, share, save, skip",
        error_messages={
            'required': 'Interaction type is required',
            'invalid_choice': 'Interaction type must be one of: view, like, comment, share, save, skip'
        }
    )
    dwell_time = serializers.FloatField(
        default=0,
        min_value=0,
        help_text="Time spent viewing the post in seconds (for analytics)",
        error_messages={
            'min_value': 'Dwell time cannot be negative'
        }
    )


class CommentCreateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'parent_comment', 'is_anonymous']
        
    post = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(),
        help_text="ID of the post to comment on",
        error_messages={
            'required': 'Post ID is required',
            'does_not_exist': 'Post with this ID does not exist'
        }
    )
    content = serializers.CharField(
        help_text="Comment content text",
        error_messages={
            'required': 'Comment content is required',
            'blank': 'Comment cannot be empty'
        }
    )
    parent_comment = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(),
        required=False,
        allow_null=True,
        help_text="ID of parent comment if this is a reply (optional)",
        error_messages={
            'does_not_exist': 'Parent comment with this ID does not exist'
        }
    )
    is_anonymous = serializers.BooleanField(
        default=False,
        help_text="Whether to post this comment anonymously"
    )


class LikeCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Like
        fields = ['id', 'user', 'post']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Like.objects.all(),
                fields=['user', 'post'],
                message="You have already liked this post."
            )
        ]
        
    post = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(),
        help_text="ID of the post to like",
        error_messages={
            'required': 'Post ID is required',
            'does_not_exist': 'Post with this ID does not exist'
        }
    )
