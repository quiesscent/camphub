"""
Utility functions and helper methods for the messaging app
"""

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Max
from django.core.cache import cache
from django.conf import settings
import re
import hashlib
from typing import List, Dict, Optional, Tuple

from .models import DirectMessage, GroupChat, GroupMessage, Notification

User = get_user_model()


def validate_message_content(content: str) -> str:
    """
    Validate and clean message content
    
    Args:
        content: Raw message content
        
    Returns:
        Cleaned message content
        
    Raises:
        ValidationError: If content is invalid
    """
    if not content or not content.strip():
        raise ValidationError("Message content cannot be empty")
    
    # Remove excessive whitespace
    content = re.sub(r'\s+', ' ', content.strip())
    
    # Check content length
    if len(content) > 5000:
        raise ValidationError("Message content is too long (max 5000 characters)")
    
    if len(content) < 1:
        raise ValidationError("Message content is too short")
    
    return content


def extract_mentions(content: str) -> List[str]:
    """
    Extract @mentions from message content
    
    Args:
        content: Message content
        
    Returns:
        List of mentioned usernames
    """
    mention_pattern = r'@([a-zA-Z0-9_]{1,30})'
    mentions = re.findall(mention_pattern, content)
    return list(set(mentions))  # Remove duplicates


def create_mention_notifications(message, mentions: List[str]) -> List[Notification]:
    """
    Create notifications for mentioned users
    
    Args:
        message: The message object (DirectMessage or GroupMessage)
        mentions: List of mentioned usernames
        
    Returns:
        List of created notifications
    """
    notifications = []
    
    for username in mentions:
        try:
            user = User.objects.get(username=username)
            
            # Don't notify the sender
            if user == message.sender:
                continue
            
            # For group messages, only notify if user is a member
            if isinstance(message, GroupMessage):
                if not message.chat.is_member(user):
                    continue
            
            # Create notification
            notification = Notification.objects.create(
                user=user,
                type='mention',
                title='You were mentioned',
                content=f'{message.sender.get_full_name() or message.sender.username} mentioned you in a message',
                actor=message.sender,
                target_object=message
            )
            notifications.append(notification)
            
        except User.DoesNotExist:
            continue
    
    return notifications


def get_user_online_status(user: User) -> Dict[str, any]:
    """
    Get user's online status
    
    Args:
        user: User object
        
    Returns:
        Dictionary with online status information
    """
    cache_key = f'user_online_{user.id}'
    last_seen = cache.get(cache_key)
    
    if last_seen:
        # User is considered online if last seen within 5 minutes
        online_threshold = timezone.now() - timezone.timedelta(minutes=5)
        is_online = last_seen > online_threshold
    else:
        is_online = False
        last_seen = None
    
    return {
        'is_online': is_online,
        'last_seen': last_seen,
        'status': 'online' if is_online else 'offline'
    }


def update_user_online_status(user: User) -> None:
    """
    Update user's online status
    
    Args:
        user: User object
    """
    cache_key = f'user_online_{user.id}'
    cache.set(cache_key, timezone.now(), timeout=300)  # 5 minutes


def get_conversation_summary(user1: User, user2: User) -> Dict[str, any]:
    """
    Get conversation summary between two users
    
    Args:
        user1: First user
        user2: Second user
        
    Returns:
        Dictionary with conversation summary
    """
    messages = DirectMessage.get_conversation_messages(user1, user2)
    
    if not messages.exists():
        return {
            'total_messages': 0,
            'unread_count': 0,
            'last_message': None,
            'participants': [user1, user2]
        }
    
    last_message = messages.first()
    unread_count = messages.filter(recipient=user1, is_read=False).count()
    
    return {
        'total_messages': messages.count(),
        'unread_count': unread_count,
        'last_message': last_message,
        'participants': [user1, user2]
    }


def get_group_chat_summary(group_chat: GroupChat, user: User) -> Dict[str, any]:
    """
    Get group chat summary for a user
    
    Args:
        group_chat: GroupChat object
        user: User object
        
    Returns:
        Dictionary with group chat summary
    """
    if not group_chat.is_member(user):
        return None
    
    messages = group_chat.group_messages.all()
    unread_count = group_chat.get_unread_count(user)
    last_message = group_chat.get_last_message()
    
    return {
        'id': group_chat.id,
        'name': group_chat.name,
        'description': group_chat.description,
        'member_count': group_chat.get_member_count(),
        'total_messages': messages.count(),
        'unread_count': unread_count,
        'last_message': last_message,
        'is_admin': group_chat.is_admin(user),
        'is_private': group_chat.is_private
    }


def search_messages(user: User, query: str, message_type: str = 'all') -> Dict[str, any]:
    """
    Search messages for a user
    
    Args:
        user: User object
        query: Search query
        message_type: Type of messages to search ('direct', 'group', 'all')
        
    Returns:
        Dictionary with search results
    """
    results = {
        'direct_messages': [],
        'group_messages': [],
        'total_count': 0
    }
    
    if len(query.strip()) < 2:
        return results
    
    # Search direct messages
    if message_type in ['direct', 'all']:
        direct_messages = DirectMessage.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).filter(
            content__icontains=query
        ).select_related('sender', 'recipient')[:20]
        
        results['direct_messages'] = list(direct_messages)
    
    # Search group messages
    if message_type in ['group', 'all']:
        user_groups = GroupChat.active.get_user_chats(user)
        group_messages = GroupMessage.objects.filter(
            chat__in=user_groups
        ).filter(
            content__icontains=query
        ).select_related('sender', 'chat')[:20]
        
        results['group_messages'] = list(group_messages)
    
    results['total_count'] = len(results['direct_messages']) + len(results['group_messages'])
    
    return results


def get_message_statistics(user: User) -> Dict[str, any]:
    """
    Get messaging statistics for a user
    
    Args:
        user: User object
        
    Returns:
        Dictionary with messaging statistics
    """
    # Direct message statistics
    sent_messages = DirectMessage.objects.filter(sender=user).count()
    received_messages = DirectMessage.objects.filter(recipient=user).count()
    unread_messages = DirectMessage.objects.filter(recipient=user, is_read=False).count()
    
    # Group message statistics
    group_messages_sent = GroupMessage.objects.filter(sender=user).count()
    active_group_chats = GroupChat.active.get_user_chats(user).count()
    
    # Notification statistics
    total_notifications = Notification.objects.filter(user=user).count()
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
    
    return {
        'direct_messages': {
            'sent': sent_messages,
            'received': received_messages,
            'unread': unread_messages,
            'total': sent_messages + received_messages
        },
        'group_messages': {
            'sent': group_messages_sent,
            'active_chats': active_group_chats
        },
        'notifications': {
            'total': total_notifications,
            'unread': unread_notifications
        }
    }


def cleanup_old_data(days: int = 30) -> Dict[str, int]:
    """
    Cleanup old messaging data
    
    Args:
        days: Number of days to keep data
        
    Returns:
        Dictionary with cleanup statistics
    """
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    
    # Cleanup old read notifications
    deleted_notifications = Notification.objects.filter(
        is_read=True,
        read_at__lt=cutoff_date
    ).delete()[0]
    
    # Cleanup old message attachments for deleted messages
    # This would require additional logic based on your attachment model
    
    return {
        'deleted_notifications': deleted_notifications,
        'cleanup_date': cutoff_date
    }


def generate_conversation_id(user1: User, user2: User) -> str:
    """
    Generate a unique conversation ID for two users
    
    Args:
        user1: First user
        user2: Second user
        
    Returns:
        Unique conversation ID
    """
    # Sort user IDs to ensure consistent conversation ID
    user_ids = sorted([user1.id, user2.id])
    conversation_string = f"{user_ids[0]}_{user_ids[1]}"
    
    # Generate hash for the conversation
    return hashlib.sha256(conversation_string.encode()).hexdigest()


def validate_group_chat_name(name: str) -> str:
    """
    Validate and clean group chat name
    
    Args:
        name: Raw group chat name
        
    Returns:
        Cleaned group chat name
        
    Raises:
        ValidationError: If name is invalid
    """
    if not name or not name.strip():
        raise ValidationError("Group chat name cannot be empty")
    
    name = name.strip()
    
    if len(name) < 2:
        raise ValidationError("Group chat name must be at least 2 characters")
    
    if len(name) > 100:
        raise ValidationError("Group chat name cannot exceed 100 characters")
    
    # Check for inappropriate characters
    if re.search(r'[<>"\']', name):
        raise ValidationError("Group chat name contains invalid characters")
    
    return name


def get_popular_group_chats(limit: int = 10) -> List[GroupChat]:
    """
    Get popular public group chats
    
    Args:
        limit: Number of chats to return
        
    Returns:
        List of popular group chats
    """
    return GroupChat.active.filter(
        is_private=False
    ).annotate(
        message_count=Count('group_messages')
    ).order_by('-message_count')[:limit]


def check_user_permissions(user: User, target_user: User) -> Dict[str, bool]:
    """
    Check user permissions for messaging
    
    Args:
        user: Current user
        target_user: Target user
        
    Returns:
        Dictionary with permission flags
    """
    # In a real implementation, you might check:
    # - If users are blocked
    # - If users are in the same institution
    # - If users have privacy settings
    
    return {
        'can_send_message': True,  # Default: all authenticated users can message
        'can_add_to_group': True,
        'is_blocked': False,
        'same_institution': True  # This would depend on your user model
    }


def format_message_content(content: str) -> str:
    """
    Format message content for display
    
    Args:
        content: Raw message content
        
    Returns:
        Formatted message content
    """
    # Convert URLs to clickable links
    url_pattern = r'https?://[^\s<>"{\|}\\^`\[\]]+'
    content = re.sub(url_pattern, r'<a href="\g<0>" target="_blank">\g<0></a>', content)
    
    # Convert mentions to links
    mention_pattern = r'@([a-zA-Z0-9_]{1,30})'
    content = re.sub(mention_pattern, r'<span class="mention">@\1</span>', content)
    
    # Convert line breaks to HTML
    content = content.replace('\n', '<br>')
    
    return content


def get_user_conversation_list(user: User, limit: int = 20) -> List[Dict[str, any]]:
    """
    Get formatted conversation list for a user
    
    Args:
        user: User object
        limit: Number of conversations to return
        
    Returns:
        List of conversation dictionaries
    """
    conversations = DirectMessage.get_user_conversations(user)
    
    formatted_conversations = []
    for conv in conversations[:limit]:
        try:
            other_user = User.objects.get(id=conv['other_user_id'])
            formatted_conversations.append({
                'other_user': {
                    'id': other_user.id,
                    'username': other_user.username,
                    'full_name': other_user.get_full_name() or other_user.username,
                    'online_status': get_user_online_status(other_user)
                },
                'last_message': conv['last_message'],
                'unread_count': conv['unread_count'],
                'conversation_id': generate_conversation_id(user, other_user)
            })
        except User.DoesNotExist:
            continue
    
    return formatted_conversations