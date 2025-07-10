from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import (
    DirectMessage, 
    GroupChat, 
    GroupChatMember, 
    GroupMessage, 
    Notification, 
    MessageAttachment
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested relationships"""
    full_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'avatar']
        read_only_fields = ['id', 'username', 'email']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
    
    def get_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return obj.profile.avatar.url
        return None


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for message attachments"""
    file_size_display = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageAttachment
        fields = [
            'id', 'filename', 'file_type', 'file_size', 
            'file_size_display', 'file_url', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_file_size_display(self, obj):
        return obj.get_file_size_display()
    
    def get_file_url(self, obj):
        return obj.file.url if obj.file else None


class DirectMessageSerializer(serializers.ModelSerializer):
    """Serializer for direct messages"""
    sender = UserBasicSerializer(read_only=True)
    recipient = UserBasicSerializer(read_only=True)
    recipient_id = serializers.IntegerField(write_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    conversation_partner = serializers.SerializerMethodField()
    formatted_created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = DirectMessage
        fields = [
            'id', 'sender', 'recipient', 'recipient_id', 'content', 
            'is_read', 'read_at', 'created_at', 'updated_at',
            'attachments', 'conversation_partner', 'formatted_created_at'
        ]
        read_only_fields = ['id', 'sender', 'is_read', 'read_at', 'created_at', 'updated_at']
    
    def get_conversation_partner(self, obj):
        request = self.context.get('request')
        if request and request.user:
            partner = obj.get_conversation_partner(request.user)
            return UserBasicSerializer(partner).data
        return None
    
    def get_formatted_created_at(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    
    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        if len(value) > 5000:
            raise serializers.ValidationError("Message content is too long")
        return value.strip()
    
    def validate_recipient_id(self, value):
        request = self.context.get('request')
        if request and request.user:
            if value == request.user.id:
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
        
        message = DirectMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            **validated_data
        )
        
        # Create notification for recipient
        Notification.create_message_notification(
            sender=request.user,
            recipient=recipient,
            message=message
        )
        
        return message


class ConversationSerializer(serializers.Serializer):
    """Serializer for conversation list"""
    other_user = UserBasicSerializer(read_only=True)
    last_message = DirectMessageSerializer(read_only=True)
    unread_count = serializers.IntegerField(read_only=True)
    last_message_time = serializers.DateTimeField(read_only=True)


class GroupChatMemberSerializer(serializers.ModelSerializer):
    """Serializer for group chat members"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = GroupChatMember
        fields = [
            'user', 'is_admin', 'is_active', 'joined_at', 
            'left_at', 'last_read_at'
        ]
        read_only_fields = ['joined_at', 'left_at', 'last_read_at']


# Simple message serializer without chat field to avoid circular reference
class SimpleGroupMessageSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = GroupMessage
        fields = ['id', 'sender', 'content', 'created_at', 'updated_at']


class GroupMessageSerializer(serializers.ModelSerializer):
    """Serializer for group messages"""
    sender = UserBasicSerializer(read_only=True)
    chat_id = serializers.CharField(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = GroupMessage
        fields = ['id', 'chat_id', 'sender', 'content', 'attachments', 'created_at', 'updated_at']
        read_only_fields = ['id', 'chat_id', 'sender', 'created_at', 'updated_at']
    
    def get_formatted_created_at(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    
    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        if len(value) > 5000:
            raise serializers.ValidationError("Message content is too long")
        return value.strip()
    
    def create(self, validated_data):
        request = self.context.get('request')
        
        message = GroupMessage.objects.create(
            **validated_data
        )
        
        # Create notifications for all group members except sender
        Notification.create_group_message_notification(
            sender=message.sender,
            group_chat=message.chat,
            message=message
        )
        
        return message


class GroupChatSerializer(serializers.ModelSerializer):
    """Serializer for group chats"""
    creator = UserBasicSerializer(read_only=True)
    members = GroupChatMemberSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    admin_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    user_is_member = serializers.SerializerMethodField()
    user_is_admin = serializers.SerializerMethodField()
    can_add_members = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupChat
        fields = [
            'id', 'name', 'description', 'creator', 'members', 
            'is_private', 'is_active', 'max_members', 'created_at', 
            'updated_at', 'member_count', 'admin_count', 'last_message',
            'unread_count', 'user_is_member', 'user_is_admin', 'can_add_members'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.get_member_count()
    
    def get_admin_count(self, obj):
        return obj.get_admin_count()
    
    def get_last_message(self, obj):
        last_message = obj.get_last_message()
        if last_message:
            return SimpleGroupMessageSerializer(last_message).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.get_unread_count(request.user)
        return 0
    
    def get_user_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.is_member(request.user)
        return False
    
    def get_user_is_admin(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.is_admin(request.user)
        return False
    
    def get_can_add_members(self, obj):
        return obj.can_add_members()
    
    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Group chat name cannot be empty")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Group chat name must be at least 2 characters")
        return value.strip()
    
    def validate_max_members(self, value):
        if value < 2:
            raise serializers.ValidationError("Group chat must allow at least 2 members")
        if value > 1000:
            raise serializers.ValidationError("Group chat cannot have more than 1000 members")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        group_chat = GroupChat.objects.create(
            creator=request.user,
            **validated_data
        )
        
        # Add creator as admin member
        group_chat.add_member(request.user, is_admin=True)
        
        return group_chat


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    actor = UserBasicSerializer(read_only=True)
    target_object_data = serializers.SerializerMethodField()
    target_url = serializers.SerializerMethodField()
    formatted_created_at = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'content', 'actor', 'is_read', 
            'read_at', 'created_at', 'target_object_data', 'target_url',
            'formatted_created_at', 'time_ago'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_target_object_data(self, obj):
        if obj.target_object:
            if isinstance(obj.target_object, DirectMessage):
                return DirectMessageSerializer(obj.target_object).data
            elif isinstance(obj.target_object, GroupMessage):
                return GroupMessageSerializer(obj.target_object).data
            elif isinstance(obj.target_object, GroupChat):
                return GroupChatSerializer(obj.target_object).data
        return None
    
    def get_target_url(self, obj):
        return obj.get_target_url()
    
    def get_formatted_created_at(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_time_ago(self, obj):
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"


class AddMemberSerializer(serializers.Serializer):
    """Serializer for adding members to group chat"""
    user_id = serializers.IntegerField()
    is_admin = serializers.BooleanField(default=False)
    
    def validate_user_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value


class RemoveMemberSerializer(serializers.Serializer):
    """Serializer for removing members from group chat"""
    user_id = serializers.IntegerField()
    
    def validate_user_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking messages/notifications as read"""
    message_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    
    def validate_message_ids(self, value):
        if value:
            # Validate that all message IDs exist
            existing_ids = DirectMessage.objects.filter(
                id__in=value
            ).values_list('id', flat=True)
            
            missing_ids = set(value) - set(existing_ids)
            if missing_ids:
                raise serializers.ValidationError(
                    f"Messages with IDs {list(missing_ids)} do not exist"
                )
        return value