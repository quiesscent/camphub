from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, Max
from django.urls import reverse
import uuid

User = get_user_model()

class ConversationManager(models.Manager):
    """Custom manager for handling direct message conversations"""
    
    def get_conversation(self, user1, user2):
        """Get or create a conversation between two users"""
        # Check if conversation already exists
        conversation = self.filter(
            Q(sender=user1, recipient=user2) | Q(sender=user2, recipient=user1)
        ).first()
        
        if not conversation:
            # Create new conversation by creating a message
            return None
        return conversation
    
    def get_user_conversations(self, user):
        """Get all conversations for a user with last message info"""
        return self.filter(
            Q(sender=user) | Q(recipient=user)
        ).select_related('sender', 'recipient').order_by('-created_at')

class DirectMessage(models.Model):
    """Model for direct messages between two users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_messages'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ConversationManager()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'recipient', '-created_at']),
            models.Index(fields=['is_read']),
        ]
        
    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"
    
    def clean(self):
        """Validate that sender and recipient are different"""
        if self.sender == self.recipient:
            raise ValidationError("Users cannot send messages to themselves")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def get_conversation_partner(self, user):
        """Get the other user in this conversation"""
        return self.recipient if self.sender == user else self.sender
    
    @classmethod
    def get_conversation_messages(cls, user1, user2):
        """Get all messages between two users"""
        return cls.objects.filter(
            Q(sender=user1, recipient=user2) | Q(sender=user2, recipient=user1)
        ).select_related('sender', 'recipient').order_by('created_at')
    
    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread messages for a user"""
        return cls.objects.filter(recipient=user, is_read=False).count()
    
    @classmethod
    def get_user_conversations(cls, user):
        """Get all conversations for a user with last message info"""
        # Get all users this user has had conversations with
        conversations = cls.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).values(
            'sender', 'recipient'
        ).annotate(
            last_message_time=Max('created_at')
        ).order_by('-last_message_time')
        
        # Get the actual last messages
        conversation_list = []
        for conv in conversations:
            if conv['sender'] == user.id:
                other_user_id = conv['recipient']
            else:
                other_user_id = conv['sender']
            
            # Skip if this is the same user (shouldn't happen due to validation)
            if other_user_id == user.id:
                continue
            
            # Get the last message between these users
            last_message = cls.objects.filter(
                Q(sender=user.id, recipient=other_user_id) | 
                Q(sender=other_user_id, recipient=user.id)
            ).select_related('sender', 'recipient').first()
            
            if last_message:
                conversation_list.append({
                    'other_user_id': other_user_id,
                    'last_message': last_message,
                    'unread_count': cls.objects.filter(
                        sender=other_user_id, recipient=user, is_read=False
                    ).count()
                })
        
        return conversation_list

class ActiveGroupChatManager(models.Manager):
    """Manager for active group chats"""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    def get_user_chats(self, user):
        """Get all group chats for a user"""
        return self.filter(members=user).select_related('creator').prefetch_related('members')

class GroupChat(models.Model):
    """Model for group chats"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_group_chats'
    )
    members = models.ManyToManyField(
        User, 
        through='GroupChatMember',
        related_name='group_chats'
    )
    is_private = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    max_members = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = models.Manager()
    active = ActiveGroupChatManager()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['creator', 'is_active']),
            models.Index(fields=['is_private', 'is_active']),
        ]
        
    def __str__(self):
        return f"Group Chat: {self.name}"
    
    def clean(self):
        """Validate group chat constraints"""
        if self.max_members < 2:
            raise ValidationError("Group chat must allow at least 2 members")
        if len(self.name.strip()) < 2:
            raise ValidationError("Group chat name must be at least 2 characters")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_member_count(self):
        """Get total number of active members"""
        return self.group_members.filter(is_active=True).count()
    
    def get_admin_count(self):
        """Get number of admin members"""
        return self.group_members.filter(is_active=True, is_admin=True).count()
    
    def can_add_members(self):
        """Check if more members can be added"""
        return self.get_member_count() < self.max_members
    
    def is_member(self, user):
        """Check if user is an active member"""
        return self.group_members.filter(user=user, is_active=True).exists()
    
    def is_admin(self, user):
        """Check if user is an admin"""
        return self.group_members.filter(user=user, is_active=True, is_admin=True).exists()
    
    def add_member(self, user, added_by=None, is_admin=False):
        """Add a user to the group chat"""
        if not self.can_add_members():
            raise ValidationError("Group chat is full")
        
        member, created = GroupChatMember.objects.get_or_create(
            chat=self,
            user=user,
            defaults={'is_admin': is_admin}
        )
        
        if not created and not member.is_active:
            member.is_active = True
            member.is_admin = is_admin
            member.save()
        
        return member
    
    def remove_member(self, user):
        """Remove a user from the group chat"""
        try:
            member = self.group_members.get(user=user, is_active=True)
            member.is_active = False
            member.save()
        except GroupChatMember.DoesNotExist:
            pass
    
    def get_last_message(self):
        """Get the last message in this group chat"""
        return self.group_messages.select_related('sender').first()
    
    def get_unread_count(self, user):
        """Get count of unread messages for a user in this group"""
        try:
            member = self.group_members.get(user=user, is_active=True)
            return self.group_messages.filter(created_at__gt=member.last_read_at).count()
        except GroupChatMember.DoesNotExist:
            return 0
    
    def update_last_read(self, user):
        """Update the last read time for a user in this group"""
        try:
            member = self.group_members.get(user=user, is_active=True)
            member.last_read_at = timezone.now()
            member.save(update_fields=['last_read_at'])
        except GroupChatMember.DoesNotExist:
            pass

class GroupChatMember(models.Model):
    """Through model for group chat membership"""
    
    chat = models.ForeignKey(
        GroupChat, 
        on_delete=models.CASCADE, 
        related_name='group_members'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='group_memberships'
    )
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    last_read_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['chat', 'user']
        indexes = [
            models.Index(fields=['chat', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]
        
    def __str__(self):
        return f"{self.user.username} in {self.chat.name}"
    
    def save(self, *args, **kwargs):
        if not self.is_active and not self.left_at:
            self.left_at = timezone.now()
        elif self.is_active and self.left_at:
            self.left_at = None
        super().save(*args, **kwargs)

class GroupMessage(models.Model):
    """Model for messages in group chats"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(
        GroupChat, 
        on_delete=models.CASCADE, 
        related_name='group_messages'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_group_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chat', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
        ]
        
    def __str__(self):
        return f"Message from {self.sender.username} in {self.chat.name}"
    
    def clean(self):
        """Validate that sender is a member of the group chat"""
        if not self.chat.is_member(self.sender):
            raise ValidationError("User is not a member of this group chat")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class UnreadNotificationManager(models.Manager):
    """Manager for unread notifications"""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_read=False)
    
    def for_user(self, user):
        """Get unread notifications for a user"""
        return self.filter(user=user).select_related('actor').order_by('-created_at')

class Notification(models.Model):
    """Model for user notifications"""
    
    NOTIFICATION_TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('message', 'Message'),
        ('group_message', 'Group Message'),
        ('event', 'Event'),
        ('follow', 'Follow'),
        ('mention', 'Mention'),
        ('group_invite', 'Group Invite'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    actor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='triggered_notifications',
        null=True, 
        blank=True
    )
    # Generic foreign key for flexible target objects - changed to handle UUIDs
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    target_object_id = models.CharField(max_length=255, null=True, blank=True)  # Changed from PositiveIntegerField
    target_object = GenericForeignKey('target_content_type', 'target_object_id')
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = models.Manager()
    unread = UnreadNotificationManager()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', 'type', '-created_at']),
            models.Index(fields=['actor', '-created_at']),
        ]
        
    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def get_target_url(self):
        """Get URL for the target object"""
        if self.target_object:
            if hasattr(self.target_object, 'get_absolute_url'):
                return self.target_object.get_absolute_url()
        return None
    
    @classmethod
    def create_message_notification(cls, sender, recipient, message):
        """Create a notification for a new direct message"""
        return cls.objects.create(
            user=recipient,
            type='message',
            title='New Message',
            content=f'{sender.get_full_name() or sender.username} sent you a message',
            actor=sender,
            target_object=message
        )
    
    @classmethod
    def create_group_message_notification(cls, sender, group_chat, message):
        """Create notifications for new group message"""
        notifications = []
        for member in group_chat.group_members.filter(is_active=True).exclude(user=sender):
            notification = cls.objects.create(
                user=member.user,
                type='group_message',
                title='New Group Message',
                content=f'{sender.get_full_name() or sender.username} sent a message in {group_chat.name}',
                actor=sender,
                target_object=message
            )
            notifications.append(notification)
        return notifications
    
    @classmethod
    def create_group_invite_notification(cls, inviter, invitee, group_chat):
        """Create a notification for group chat invitation"""
        return cls.objects.create(
            user=invitee,
            type='group_invite',
            title='Group Chat Invitation',
            content=f'{inviter.get_full_name() or inviter.username} invited you to join {group_chat.name}',
            actor=inviter,
            target_object=group_chat
        )
    
    @classmethod
    def mark_all_as_read(cls, user):
        """Mark all notifications as read for a user"""
        unread_notifications = cls.objects.filter(user=user, is_read=False)
        count = unread_notifications.count()
        unread_notifications.update(is_read=True, read_at=timezone.now())
        return count
    
    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread notifications for a user"""
        return cls.objects.filter(user=user, is_read=False).count()
    
    @classmethod
    def cleanup_old_notifications(cls, days=30):
        """Clean up old read notifications"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return cls.objects.filter(
            is_read=True,
            read_at__lt=cutoff_date
        ).delete()

# Optional: Model for message attachments
class MessageAttachment(models.Model):
    """Model for message attachments"""
    
    ATTACHMENT_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('audio', 'Audio'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Generic foreign key to attach to both direct and group messages - fixed for UUIDs
    message_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    message_object_id = models.CharField(max_length=255)  # Changed from PositiveIntegerField
    message_object = GenericForeignKey('message_content_type', 'message_object_id')
    
    file = models.FileField(upload_to='message_attachments/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES)
    file_size = models.PositiveIntegerField()  # in bytes
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='uploaded_attachments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['message_content_type', 'message_object_id']),
            models.Index(fields=['uploaded_by', '-created_at']),
        ]
    
    def __str__(self):
        return f"Attachment: {self.filename}"
    
    def get_file_size_display(self):
        """Get human-readable file size"""
        if not self.file_size:
            return "0 B"
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"