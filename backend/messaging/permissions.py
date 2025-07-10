from rest_framework import permissions
from rest_framework.permissions import BasePermission
from .models import GroupChat, GroupChatMember, DirectMessage, Notification


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.sender == request.user


class IsDirectMessageParticipant(BasePermission):
    """
    Custom permission for direct message participants.
    """
    def has_object_permission(self, request, view, obj):
        # Only sender or recipient can access the message
        return obj.sender == request.user or obj.recipient == request.user


class IsGroupChatMember(BasePermission):
    """
    Custom permission for group chat members.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is an active member of the group chat
        if isinstance(obj, GroupChat):
            return obj.is_member(request.user)
        return False


class IsGroupChatAdmin(BasePermission):
    """
    Custom permission for group chat admins.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is an admin of the group chat
        if isinstance(obj, GroupChat):
            return obj.is_admin(request.user)
        return False


class IsGroupChatCreatorOrAdmin(BasePermission):
    """
    Custom permission for group chat creator or admins.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is creator or admin of the group chat
        if isinstance(obj, GroupChat):
            return obj.creator == request.user or obj.is_admin(request.user)
        return False


class IsNotificationOwner(BasePermission):
    """
    Custom permission for notification owners.
    """
    def has_object_permission(self, request, view, obj):
        # Only the notification recipient can access it
        return obj.user == request.user


class CanSendDirectMessage(BasePermission):
    """
    Custom permission to check if user can send direct messages.
    """
    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Additional checks can be added here (e.g., user verification, blocking)
        # For now, any authenticated user can send messages
        return True


class CanCreateGroupChat(BasePermission):
    """
    Custom permission to check if user can create group chats.
    """
    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Additional checks can be added here (e.g., user verification, limits)
        # For now, any authenticated user can create group chats
        return True


class CanJoinGroupChat(BasePermission):
    """
    Custom permission to check if user can join group chats.
    """
    def has_object_permission(self, request, view, obj):
        # User must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if group chat is active
        if not obj.is_active:
            return False
        
        # Check if user is already a member
        if obj.is_member(request.user):
            return False
        
        # Check if group chat is full
        if not obj.can_add_members():
            return False
        
        # For private groups, only admins can add members
        if obj.is_private:
            return False
        
        return True


class CanManageGroupChatMembers(BasePermission):
    """
    Custom permission to check if user can manage group chat members.
    """
    def has_object_permission(self, request, view, obj):
        # User must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Only creator or admins can manage members
        return obj.creator == request.user or obj.is_admin(request.user)


class CanDeleteGroupChat(BasePermission):
    """
    Custom permission to check if user can delete group chats.
    """
    def has_object_permission(self, request, view, obj):
        # Only creator can delete group chat
        return obj.creator == request.user


class CanModifyGroupChat(BasePermission):
    """
    Custom permission to check if user can modify group chat details.
    """
    def has_object_permission(self, request, view, obj):
        # Creator or admins can modify group chat
        return obj.creator == request.user or obj.is_admin(request.user)


class MessageRateLimit(BasePermission):
    """
    Custom permission to implement message rate limiting.
    """
    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Implement rate limiting logic here
        # For now, we'll allow all messages
        # In production, you might want to implement Redis-based rate limiting
        return True


class IsInstitutionVerified(BasePermission):
    """
    Custom permission to check if user is institution verified.
    """
    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if user has verified institutional email
        # This would depend on your user model structure
        # For now, we'll allow all authenticated users
        return True


class CanAccessPrivateGroupChat(BasePermission):
    """
    Custom permission to check if user can access private group chats.
    """
    def has_object_permission(self, request, view, obj):
        # For private group chats, only members can access
        if obj.is_private:
            return obj.is_member(request.user)
        
        # For public group chats, any authenticated user can view
        return request.user.is_authenticated


class CanSendGroupMessage(BasePermission):
    """
    Custom permission to check if user can send messages in group chat.
    """
    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if user is trying to send a message
        if request.method == 'POST':
            chat_id = request.data.get('chat_id')
            if chat_id:
                try:
                    chat = GroupChat.objects.get(id=chat_id)
                    return chat.is_member(request.user)
                except GroupChat.DoesNotExist:
                    return False
        
        return True


class CanMarkAsRead(BasePermission):
    """
    Custom permission to check if user can mark messages as read.
    """
    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Users can only mark their own received messages as read
        return True
    
    def has_object_permission(self, request, view, obj):
        # For direct messages, only recipient can mark as read
        if isinstance(obj, DirectMessage):
            return obj.recipient == request.user
        
        # For notifications, only owner can mark as read
        if isinstance(obj, Notification):
            return obj.user == request.user
        
        return False


class CanDeleteMessage(BasePermission):
    """
    Custom permission to check if user can delete messages.
    """
    def has_object_permission(self, request, view, obj):
        # Only message sender can delete their own messages
        return obj.sender == request.user


class CanViewConversation(BasePermission):
    """
    Custom permission to check if user can view conversation.
    """
    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Users can only view their own conversations
        return True