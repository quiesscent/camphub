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


class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'created_at']


class ShareSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Share
        fields = ['id', 'user', 'post', 'caption', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    media = PostMediaSerializer(many=True, read_only=True)
    course = serializers.StringRelatedField()
    location = serializers.StringRelatedField()
    
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), source='course', write_only=True, required=False, allow_null=True
    )
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Campus.objects.all(), source='location', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content', 'post_type', 'visibility', 
            'course', 'location', 'is_pinned', 'is_anonymous', 
            'created_at', 'updated_at', 'media',
            'likes_count', 'comments_count', 'is_liked',
            'course_id', 'location_id'
        ]
        read_only_fields = ('author', 'created_at', 'updated_at', 'media')

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(post=obj, user=request.user).exists()
        return False

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        # Note: Media files should be handled separately in the view.
        # For example, after creating the post, create PostMedia objects from request.FILES
        return Post.objects.create(**validated_data)


class UserInteractionCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserInteraction
        fields = ['id', 'user', 'post', 'interaction_type', 'duration_seconds']


class CommentCreateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'parent_comment', 'is_anonymous']


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
