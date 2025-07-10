from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Max, Prefetch
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.http import Http404

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from .models import (
    DirectMessage, 
    GroupChat, 
    GroupChatMember, 
    GroupMessage, 
    Notification,
    MessageAttachment
)
from .serializers import (
    DirectMessageSerializer,
    ConversationSerializer,
    GroupChatSerializer,
    GroupMessageSerializer,
    NotificationSerializer,
    AddMemberSerializer,
    RemoveMemberSerializer,
    MarkAsReadSerializer,
    GroupChatMemberSerializer
)
from .permissions import (
    IsDirectMessageParticipant,
    IsGroupChatMember,
    IsGroupChatCreatorOrAdmin,
    IsNotificationOwner,
    CanSendDirectMessage,
    CanCreateGroupChat,
    CanManageGroupChatMembers,
    CanSendGroupMessage,
    CanMarkAsRead,
    CanViewConversation
)

User = get_user_model()


class StandardResultPagination(PageNumberPagination):
    """Standard pagination for messaging endpoints"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class DirectMessageListCreateView(generics.ListCreateAPIView):
    """
    List direct messages for a conversation and create new messages
    """
    serializer_class = DirectMessageSerializer
    permission_classes = [IsAuthenticated, CanSendDirectMessage]
    pagination_class = StandardResultPagination
    
    def get_queryset(self):
        user = self.request.user
        other_user_id = self.request.query_params.get('other_user')
        
        if other_user_id:
            try:
                other_user = User.objects.get(id=other_user_id)
                return DirectMessage.get_conversation_messages(user, other_user)
            except User.DoesNotExist:
                return DirectMessage.objects.none()
        
        # Return all messages for the user
        return DirectMessage.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).select_related('sender', 'recipient')
    
    def perform_create(self, serializer):
        serializer.save()
        
        # Mark all previous messages from recipient as read
        recipient_id = serializer.validated_data.get('recipient_id')
        if recipient_id:
            DirectMessage.objects.filter(
                sender_id=recipient_id,
                recipient=self.request.user,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())


class DirectMessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a direct message
    """
    queryset = DirectMessage.objects.all()
    serializer_class = DirectMessageSerializer
    permission_classes = [IsAuthenticated, IsDirectMessageParticipant]
    
    def perform_update(self, serializer):
        # Only sender can update their own messages
        if serializer.instance.sender != self.request.user:
            raise ValidationError("You can only edit your own messages")
        serializer.save()
    
    def perform_destroy(self, instance):
        # Only sender can delete their own messages
        if instance.sender != self.request.user:
            raise ValidationError("You can only delete your own messages")
        instance.delete()


class ConversationListView(generics.ListAPIView):
    """
    List all conversations for the authenticated user
    """
    permission_classes = [IsAuthenticated, CanViewConversation]
    pagination_class = StandardResultPagination
    
    def get(self, request, *args, **kwargs):
        user = request.user
        conversations = DirectMessage.get_user_conversations(user)
        
        # Transform the data for the response
        conversation_data = []
        for conv in conversations:
            try:
                other_user = User.objects.get(id=conv['other_user_id'])
                conversation_data.append({
                    'other_user': other_user,
                    'last_message': conv['last_message'],
                    'unread_count': conv['unread_count'],
                    'last_message_time': conv['last_message'].created_at
                })
            except User.DoesNotExist:
                continue
        
        # Sort by last message time
        conversation_data.sort(key=lambda x: x['last_message_time'], reverse=True)
        
        # Paginate the results
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(conversation_data, request)
        
        serializer = ConversationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class MarkMessageAsReadView(APIView):
    """
    Mark direct messages as read
    """
    permission_classes = [IsAuthenticated, CanMarkAsRead]
    
    def post(self, request):
        serializer = MarkAsReadSerializer(data=request.data)
        if serializer.is_valid():
            message_ids = serializer.validated_data.get('message_ids', [])
            
            if message_ids:
                # Mark specific messages as read
                messages = DirectMessage.objects.filter(
                    id__in=message_ids,
                    recipient=request.user,
                    is_read=False
                )
                for message in messages:
                    message.mark_as_read()
                count = messages.count()
            else:
                # Mark all unread messages as read
                messages = DirectMessage.objects.filter(
                    recipient=request.user,
                    is_read=False
                )
                for message in messages:
                    message.mark_as_read()
                count = messages.count()
            
            return Response({
                'success': True,
                'message': f'Marked {count} messages as read',
                'count': count
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GroupChatListCreateView(generics.ListCreateAPIView):
    """
    List group chats and create new ones
    """
    serializer_class = GroupChatSerializer
    permission_classes = [IsAuthenticated, CanCreateGroupChat]
    pagination_class = StandardResultPagination
    
    def get_queryset(self):
        user = self.request.user
        return GroupChat.active.get_user_chats(user)
    
    def perform_create(self, serializer):
        serializer.save()


class GroupChatDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a group chat
    """
    queryset = GroupChat.objects.all()
    serializer_class = GroupChatSerializer
    permission_classes = [IsAuthenticated, IsGroupChatMember]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticated(), IsGroupChatCreatorOrAdmin()]
        elif self.request.method == 'DELETE':
            return [IsAuthenticated(), IsGroupChatCreatorOrAdmin()]
        return super().get_permissions()
    
    def perform_update(self, serializer):
        serializer.save()
    
    def perform_destroy(self, instance):
        # Soft delete - mark as inactive
        instance.is_active = False
        instance.save()


class GroupChatMemberView(APIView):
    """
    Manage group chat members
    """
    permission_classes = [IsAuthenticated, CanManageGroupChatMembers]
    
    def post(self, request, chat_id):
        """Add a member to the group chat"""
        try:
            chat = GroupChat.objects.get(id=chat_id)
            self.check_object_permissions(request, chat)
            
            serializer = AddMemberSerializer(data=request.data)
            if serializer.is_valid():
                user_id = serializer.validated_data['user_id']
                is_admin = serializer.validated_data.get('is_admin', False)
                
                try:
                    user = User.objects.get(id=user_id)
                    member = chat.add_member(user, added_by=request.user, is_admin=is_admin)
                    
                    # Create notification for the added user
                    Notification.create_group_invite_notification(
                        inviter=request.user,
                        invitee=user,
                        group_chat=chat
                    )
                    
                    return Response({
                        'success': True,
                        'message': f'Added {user.username} to group chat',
                        'member': GroupChatMemberSerializer(member).data
                    })
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'User not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                except ValidationError as e:
                    # Log the exception details for debugging purposes
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error("Validation error occurred: %s", str(e))
                    return Response({
                        'success': False,
                        'error': 'Invalid input. Please check your data and try again.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except GroupChat.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Group chat not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, chat_id):
        """Remove a member from the group chat"""
        try:
            chat = GroupChat.objects.get(id=chat_id)
            self.check_object_permissions(request, chat)
            
            serializer = RemoveMemberSerializer(data=request.data)
            if serializer.is_valid():
                user_id = serializer.validated_data['user_id']
                
                try:
                    user = User.objects.get(id=user_id)
                    chat.remove_member(user)
                    
                    return Response({
                        'success': True,
                        'message': f'Removed {user.username} from group chat'
                    })
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'User not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except GroupChat.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Group chat not found'
            }, status=status.HTTP_404_NOT_FOUND)


class GroupChatMessagesView(generics.ListCreateAPIView):
    """
    List and create messages in a group chat
    """
    serializer_class = GroupMessageSerializer
    permission_classes = [IsAuthenticated, CanSendGroupMessage]
    pagination_class = StandardResultPagination
    
    def get_queryset(self):
        chat_id = self.kwargs.get('chat_id')
        try:
            chat = GroupChat.objects.get(id=chat_id)
            # Check if user is a member
            if not chat.is_member(self.request.user):
                return GroupMessage.objects.none()
            
            # Update user's last read time
            chat.update_last_read(self.request.user)
            
            return chat.group_messages.select_related('sender')
        except GroupChat.DoesNotExist:
            return GroupMessage.objects.none()
    
    def perform_create(self, serializer):
        chat_id = self.kwargs.get('chat_id')
        try:
            chat = GroupChat.objects.get(id=chat_id)
            if not chat.is_member(self.request.user):
                raise ValidationError("You are not a member of this group chat")
            
            # Save with the chat from the URL parameter
            message = serializer.save(sender=self.request.user, chat=chat)
            
        except GroupChat.DoesNotExist:
            raise ValidationError("Group chat not found")


class GroupMessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a group message
    """
    queryset = GroupMessage.objects.all()
    serializer_class = GroupMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        obj = super().get_object()
        # Check if user is a member of the group chat
        if not obj.chat.is_member(self.request.user):
            raise Http404("Message not found")
        return obj
    
    def perform_update(self, serializer):
        # Only sender can update their own messages
        if serializer.instance.sender != self.request.user:
            raise ValidationError("You can only edit your own messages")
        serializer.save()
    
    def perform_destroy(self, instance):
        # Only sender can delete their own messages
        if instance.sender != self.request.user:
            raise ValidationError("You can only delete your own messages")
        instance.delete()


class NotificationListView(generics.ListAPIView):
    """
    List notifications for the authenticated user
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultPagination
    
    def get_queryset(self):
        user = self.request.user
        notification_type = self.request.query_params.get('type')
        unread_only = self.request.query_params.get('unread_only', 'false').lower() == 'true'
        
        queryset = Notification.objects.filter(user=user).select_related('actor')
        
        if notification_type:
            queryset = queryset.filter(type=notification_type)
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        return queryset


class NotificationDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update a notification
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsNotificationOwner]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        # Only allow marking as read
        if 'is_read' in serializer.validated_data:
            if serializer.validated_data['is_read']:
                serializer.instance.mark_as_read()
        serializer.save()


class MarkNotificationAsReadView(APIView):
    """
    Mark specific notifications as read
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=request.user
            )
            notification.mark_as_read()
            
            return Response({
                'success': True,
                'message': 'Notification marked as read'
            })
        except Notification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)


class MarkAllNotificationsAsReadView(APIView):
    """
    Mark all notifications as read for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        count = Notification.mark_all_as_read(request.user)
        
        return Response({
            'success': True,
            'message': f'Marked {count} notifications as read',
            'count': count
        })


class UnreadCountView(APIView):
    """
    Get unread counts for messages and notifications
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        unread_messages = DirectMessage.get_unread_count(user)
        unread_notifications = Notification.get_unread_count(user)
        
        # Get unread counts for each group chat
        user_groups = GroupChat.active.get_user_chats(user)
        group_unread = {}
        for group in user_groups:
            group_unread[str(group.id)] = group.get_unread_count(user)
        
        return Response({
            'success': True,
            'data': {
                'unread_messages': unread_messages,
                'unread_notifications': unread_notifications,
                'group_unread': group_unread,
                'total_unread': unread_messages + unread_notifications + sum(group_unread.values())
            }
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):
    """
    Search for users to start conversations or add to groups
    """
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return Response({
            'success': False,
            'error': 'Search query must be at least 2 characters'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(id=request.user.id)[:10]  # Limit to 10 results
    
    from .serializers import UserBasicSerializer
    serializer = UserBasicSerializer(users, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_group_chat(request, chat_id):
    """
    Join a public group chat
    """
    try:
        chat = GroupChat.objects.get(id=chat_id)
        
        # Check if group is public
        if chat.is_private:
            return Response({
                'success': False,
                'error': 'This is a private group chat'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user is already a member
        if chat.is_member(request.user):
            return Response({
                'success': False,
                'error': 'You are already a member of this group'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if group is full
        if not chat.can_add_members():
            return Response({
                'success': False,
                'error': 'Group chat is full'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add user to group
        member = chat.add_member(request.user)
        
        return Response({
            'success': True,
            'message': f'Successfully joined {chat.name}',
            'member': GroupChatMemberSerializer(member).data
        })
    
    except GroupChat.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Group chat not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leave_group_chat(request, chat_id):
    """
    Leave a group chat
    """
    try:
        chat = GroupChat.objects.get(id=chat_id)
        
        # Check if user is a member
        if not chat.is_member(request.user):
            return Response({
                'success': False,
                'error': 'You are not a member of this group'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove user from group
        chat.remove_member(request.user)
        
        return Response({
            'success': True,
            'message': f'Successfully left {chat.name}'
        })
    
    except GroupChat.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Group chat not found'
        }, status=status.HTTP_404_NOT_FOUND)
