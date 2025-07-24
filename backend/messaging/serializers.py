from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from .models import (
    DirectMessage, GroupChat, GroupChatMember, GroupMessage, 
    Notification, MessageAttachment
)
from .utils import validate_message_content, validate_group_chat_name

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for messaging contexts"""
    is_online = serializers.SerializerMethodField()
    last_seen = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 
            'profile_picture', 'is_online', 'last_seen'
        ]
        
    username = serializers.CharField(
        read_only=True,
        help_text="Unique username for identification"
    )
    first_name = serializers.CharField(
        read_only=True,
        help_text="User's first name"
    )
    last_name = serializers.CharField(
        read_only=True,
        help_text="User's last name"
    )
    profile_picture = serializers.ImageField(
        read_only=True,
        help_text="URL to user's profile picture"
    )
    is_online = serializers.BooleanField(
        read_only=True,
        help_text="Whether user is currently online (within last 5 minutes)"
    )
    last_seen = serializers.DateTimeField(
        read_only=True,
        help_text="Timestamp when user was last seen online"
    )
    
    def get_is_online(self, obj):
        from .utils import get_user_online_status
        return get_user_online_status(obj)['is_online']
    
    def get_last_seen(self, obj):
        from .utils import get_user_online_status
        return get_user_online_status(obj)['last_seen']


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for message attachments"""
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageAttachment
        fields = [
            'id', 'filename', 'file_type', 'file', 
            'file_size', 'file_size_display', 'created_at'
        ]
        
    filename = serializers.CharField(
        read_only=True,
        help_text="Original filename of the uploaded file"
    )
    file_type = serializers.ChoiceField(
        choices=MessageAttachment.ATTACHMENT_TYPES,
        read_only=True,
        help_text="Type of attachment: image, video, document, audio"
    )
    file = serializers.FileField(
        read_only=True,
        help_text="URL to the uploaded file"
    )
    file_size = serializers.IntegerField(
        read_only=True,
        help_text="File size in bytes"
    )
    file_size_display = serializers.CharField(
        read_only=True,
        help_text="Human-readable file size (e.g., '2.5 MB')"
    )
    
    def get_file_size_display(self, obj):
        return obj.get_file_size_display()


class DirectMessageSerializer(serializers.ModelSerializer):
    """Serializer for direct messages with full user information"""
    sender = UserBasicSerializer(read_only=True)
    recipient = UserBasicSerializer(read_only=True)
    recipient_id = serializers.IntegerField(
        write_only=True,
        help_text="ID of the user to send the message to",
        error_messages={
            'required': 'Recipient is required',
            'invalid': 'Invalid recipient ID'
        }
    )
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = DirectMessage
        fields = [
            'id', 'sender', 'recipient', 'recipient_id', 'content',
            'is_read', 'read_at', 'created_at', 'updated_at', 'attachments'
        ]
        read_only_fields = ['id', 'sender', 'is_read', 'read_at', 'created_at', 'updated_at']
        
    content = serializers.CharField(
        max_length=5000,
        help_text="Message content (max 5000 characters, supports @mentions)",
        error_messages={
            'required': 'Message content is required',
            'blank': 'Message content cannot be empty',
            'max_length': 'Message content cannot exceed 5000 characters'
        }
    )
    is_read = serializers.BooleanField(
        read_only=True,
        help_text="Whether the message has been read by the recipient"
    )
    read_at = serializers.DateTimeField(
        read_only=True,
        help_text="Timestamp when the message was read (null if unread)"
    )
    
    def validate_content(self, value):
        return validate_message_content(value)
    
    def validate_recipient_id(self, value):
        request = self.context.get('request')
        if request and request.user.id == value:
            raise serializers.ValidationError("Cannot send message to yourself")
        
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Recipient does not exist")
            
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        recipient_id = validated_data.pop('recipient_id')
        recipient = User.objects.get(id=recipient_id)
        
        return DirectMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            **validated_data
        )


class ConversationSerializer(serializers.Serializer):
    """Serializer for conversation list with last message info"""
    other_user = UserBasicSerializer(read_only=True)
    last_message = DirectMessageSerializer(read_only=True)
    unread_count = serializers.IntegerField(
        read_only=True,
        help_text="Number of unread messages in this conversation"
    )
    last_message_time = serializers.DateTimeField(
        read_only=True,
        help_text="Timestamp of the most recent message"
    )


class GroupChatMemberSerializer(serializers.ModelSerializer):
    """Serializer for group chat members"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = GroupChatMember
        fields = [
            'user', 'is_admin', 'is_active', 'joined_at', 
            'left_at', 'last_read_at'
        ]
        
    is_admin = serializers.BooleanField(
        read_only=True,
        help_text="Whether this member has admin privileges"
    )
    is_active = serializers.BooleanField(
        read_only=True,
        help_text="Whether this member is currently active in the group"
    )
    joined_at = serializers.DateTimeField(
        read_only=True,
        help_text="When the member joined the group"
    )
    left_at = serializers.DateTimeField(
        read_only=True,
        help_text="When the member left the group (null if still active)"
    )
    last_read_at = serializers.DateTimeField(
        read_only=True,
        help_text="Last time member read messages in this group"
    )


class GroupChatSerializer(serializers.ModelSerializer):
    """Serializer for group chats with member and message information"""
    creator = UserBasicSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    members = GroupChatMemberSerializer(
        source='group_members',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = GroupChat
        fields = [
            'id', 'name', 'description', 'creator', 'member_count',
            'is_private', 'is_active', 'max_members', 'user_role',
            'last_message', 'unread_count', 'members',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']
        
    name = serializers.CharField(
        max_length=100,
        help_text="Group chat name (2-100 characters)",
        error_messages={
            'required': 'Group name is required',
            'blank': 'Group name cannot be empty',
            'max_length': 'Group name cannot exceed 100 characters'
        }
    )
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Optional group description (max 500 characters)",
        error_messages={
            'max_length': 'Description cannot exceed 500 characters'
        }
    )
    is_private = serializers.BooleanField(
        default=False,
        help_text="Whether the group is private (invitation-only) or public"
    )
    max_members = serializers.IntegerField(
        default=100,
        min_value=2,
        max_value=500,
        help_text="Maximum number of members allowed (2-500)",
        error_messages={
            'min_value': 'Group must allow at least 2 members',
            'max_value': 'Group cannot have more than 500 members'
        }
    )
    member_count = serializers.IntegerField(
        read_only=True,
        help_text="Current number of active members"
    )
    user_role = serializers.CharField(
        read_only=True,
        help_text="Current user's role in the group: member, admin, or creator"
    )
    unread_count = serializers.IntegerField(
        read_only=True,
        help_text="Number of unread messages for current user"
    )
    
    def validate_name(self, value):
        return validate_group_chat_name(value)
    
    def get_member_count(self, obj):
        return obj.get_member_count()
    
    def get_user_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
            
        user = request.user
        if obj.creator == user:
            return 'creator'
        elif obj.is_admin(user):
            return 'admin'
        elif obj.is_member(user):
            return 'member'
        return None
    
    def get_last_message(self, obj):
        last_message = obj.get_last_message()
        if last_message:
            return {
                'content': last_message.content[:100] + '...' if len(last_message.content) > 100 else last_message.content,
                'sender': last_message.sender.username,
                'created_at': last_message.created_at
            }
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count(request.user)
        return 0
    
    def create(self, validated_data):
        request = self.context.get('request')
        group = GroupChat.objects.create(
            creator=request.user,
            **validated_data
        )
        # Add creator as admin member
        group.add_member(request.user, is_admin=True)
        return group


class GroupMessageSerializer(serializers.ModelSerializer):
    """Serializer for group messages"""
    sender = UserBasicSerializer(read_only=True)
    chat = GroupChatSerializer(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    mentions = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupMessage
        fields = [
            'id', 'chat', 'sender', 'content', 'mentions',
            'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'chat', 'sender', 'created_at', 'updated_at']
        
    content = serializers.CharField(
        max_length=5000,
        help_text="Message content (max 5000 characters, supports @mentions)",
        error_messages={
            'required': 'Message content is required',
            'blank': 'Message content cannot be empty',
            'max_length': 'Message content cannot exceed 5000 characters'
        }
    )
    mentions = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        help_text="List of usernames mentioned in this message"
    )
    
    def validate_content(self, value):
        return validate_message_content(value)
    
    def get_mentions(self, obj):
        from .utils import extract_mentions
        return extract_mentions(obj.content)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for user notifications"""
    actor = UserBasicSerializer(read_only=True)
    target_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'content', 'actor',
            'target_url', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        
    type = serializers.ChoiceField(
        choices=Notification.NOTIFICATION_TYPES,
        read_only=True,
        help_text="Type of notification: message, group_message, group_invite, mention, etc."
    )
    title = serializers.CharField(
        read_only=True,
        help_text="Notification title/subject"
    )
    content = serializers.CharField(
        read_only=True,
        help_text="Detailed notification content"
    )
    target_url = serializers.CharField(
        read_only=True,
        help_text="URL to navigate to when notification is clicked"
    )
    is_read = serializers.BooleanField(
        help_text="Whether the notification has been read"
    )
    read_at = serializers.DateTimeField(
        read_only=True,
        help_text="Timestamp when notification was read"
    )
    
    def get_target_url(self, obj):
        return obj.get_target_url()


class AddMemberSerializer(serializers.Serializer):
    """Serializer for adding members to group chats"""
    user_id = serializers.IntegerField(
        help_text="ID of the user to add to the group",
        error_messages={
            'required': 'User ID is required',
            'invalid': 'Invalid user ID'
        }
    )
    is_admin = serializers.BooleanField(
        default=False,
        help_text="Whether to add the user as an admin (default: False)"
    )
    
    def validate_user_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value


class RemoveMemberSerializer(serializers.Serializer):
    """Serializer for removing members from group chats"""
    user_id = serializers.IntegerField(
        help_text="ID of the user to remove from the group",
        error_messages={
            'required': 'User ID is required',
            'invalid': 'Invalid user ID'
        }
    )
    
    def validate_user_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking messages as read"""
    message_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        help_text="List of message IDs to mark as read (empty list marks all unread messages)",
        error_messages={
            'invalid': 'Invalid message ID format'
        }
    )
    
    def validate_message_ids(self, value):
        if value:
            # Validate that all message IDs exist and belong to the current user
            request = self.context.get('request')
            if request:
                existing_messages = DirectMessage.objects.filter(
                    id__in=value,
                    recipient=request.user
                ).values_list('id', flat=True)
                
                if len(existing_messages) != len(value):
                    raise serializers.ValidationError("Some message IDs are invalid or don't belong to you")
        
        return value


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file uploads in messages"""
    file = serializers.FileField(
        help_text="File to upload (max 10MB, supports images, videos, documents)",
        error_messages={
            'required': 'File is required',
            'invalid': 'Invalid file format'
        }
    )
    caption = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Optional caption for the file",
        error_messages={
            'max_length': 'Caption cannot exceed 255 characters'
        }
    )
    
    def validate_file(self, value):
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 10MB")
        
        # Validate file type
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'video/mp4', 'video/webm', 'video/ogg',
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("File type not supported")
        
        return value