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

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import OpenApiResponse
from drf_spectacular.types import OpenApiTypes

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
    
    @extend_schema(
        description="Get direct messages for a conversation or create a new message. Supports real-time messaging with automatic read status updates.",
        parameters=[
            OpenApiParameter(
                name='other_user',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the other user in the conversation to filter messages',
                required=False
            ),
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Page number for pagination (default: 1)',
                required=False
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of messages per page (max: 100, default: 20)',
                required=False
            )
        ],
        request=DirectMessageSerializer,
        responses={
            200: OpenApiResponse(
                description="Messages retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "count": 15,
                            "next": "http://api.example.com/api/v1/messaging/messages/?page=2",
                            "previous": None,
                            "results": [
                                {
                                    "id": "123e4567-e89b-12d3-a456-426614174000",
                                    "sender": {
                                        "id": 1,
                                        "username": "john_doe",
                                        "first_name": "John",
                                        "last_name": "Doe",
                                        "profile_picture": "/media/profiles/john.jpg"
                                    },
                                    "recipient": {
                                        "id": 2,
                                        "username": "jane_smith",
                                        "first_name": "Jane",
                                        "last_name": "Smith"
                                    },
                                    "content": "Hey, how are you doing?",
                                    "is_read": False,
                                    "read_at": None,
                                    "created_at": "2024-01-01T10:30:00Z",
                                    "updated_at": "2024-01-01T10:30:00Z"
                                }
                            ]
                        }
                    )
                ]
            ),
            201: OpenApiResponse(
                description="Message sent successfully",
                examples=[
                    OpenApiExample(
                        "Message Sent",
                        value={
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "sender": {
                                "id": 1,
                                "username": "john_doe",
                                "first_name": "John",
                                "last_name": "Doe"
                            },
                            "recipient": {
                                "id": 2,
                                "username": "jane_smith",
                                "first_name": "Jane",
                                "last_name": "Smith"
                            },
                            "content": "Hello! How's your day going?",
                            "is_read": False,
                            "created_at": "2024-01-01T10:30:00Z"
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
                            "recipient": ["This field is required"],
                            "content": ["Message content cannot be empty"]
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - cannot message this user")
        },
        tags=['Direct Messages'],
        examples=[
            OpenApiExample(
                "Send Message",
                value={
                    "recipient": 2,
                    "content": "Hello! How's your day going?"
                }
            ),
            OpenApiExample(
                "Send Message with Attachment",
                value={
                    "recipient": 2,
                    "content": "Check out this file I'm sharing!",
                    "attachment_ids": ["att-123", "att-456"]
                }
            )
        ]
    )
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
    
    @extend_schema(
        description="Get, update, or delete a specific direct message. Only message participants can access, and only sender can modify.",
        responses={
            200: OpenApiResponse(
                description="Message retrieved/updated successfully",
                response=DirectMessageSerializer
            ),
            204: OpenApiResponse(description="Message deleted successfully"),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not message participant or sender"),
            404: OpenApiResponse(description="Message not found")
        },
        tags=['Direct Messages']
    )
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
    
    @extend_schema(
        description="Get all active conversations for the authenticated user with last message info and unread counts",
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search conversations by participant name or username',
                required=False
            ),
            OpenApiParameter(
                name='unread_only',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter to show only conversations with unread messages',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Conversations retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "count": 5,
                            "next": None,
                            "previous": None,
                            "results": [
                                {
                                    "other_user": {
                                        "id": 2,
                                        "username": "jane_smith",
                                        "first_name": "Jane",
                                        "last_name": "Smith",
                                        "profile_picture": "/media/profiles/jane.jpg",
                                        "is_online": True,
                                        "last_seen": "2024-01-01T10:25:00Z"
                                    },
                                    "last_message": {
                                        "id": "123e4567-e89b-12d3-a456-426614174000",
                                        "content": "See you tomorrow!",
                                        "sender": {
                                            "id": 2,
                                            "username": "jane_smith"
                                        },
                                        "created_at": "2024-01-01T10:15:00Z",
                                        "is_read": False
                                    },
                                    "unread_count": 3,
                                    "last_message_time": "2024-01-01T10:15:00Z"
                                }
                            ]
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Direct Messages']
    )
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
    
    @extend_schema(
        description="Mark specific direct messages or all unread messages as read for the authenticated user",
        request=MarkAsReadSerializer,
        responses={
            200: OpenApiResponse(
                description="Messages marked as read successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "message": "Marked 5 messages as read",
                            "count": 5
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Direct Messages'],
        examples=[
            OpenApiExample(
                "Mark Specific Messages",
                value={
                    "message_ids": [
                        "123e4567-e89b-12d3-a456-426614174000",
                        "456e7890-e89b-12d3-a456-426614174001"
                    ]
                }
            ),
            OpenApiExample(
                "Mark All Unread",
                value={
                    "message_ids": []
                }
            )
        ]
    )
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
    
    @extend_schema(
        description="Get user's group chats or create a new group chat. Supports both public and private groups with member management.",
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search group chats by name or description',
                required=False
            ),
            OpenApiParameter(
                name='is_private',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by private/public group chats',
                required=False
            ),
            OpenApiParameter(
                name='is_admin',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter to show only groups where user is admin',
                required=False
            )
        ],
        request=GroupChatSerializer,
        responses={
            200: OpenApiResponse(
                description="Group chats retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "count": 3,
                            "results": [
                                {
                                    "id": "123e4567-e89b-12d3-a456-426614174000",
                                    "name": "CS Study Group",
                                    "description": "Group for Computer Science students",
                                    "creator": {
                                        "id": 1,
                                        "username": "john_doe",
                                        "first_name": "John",
                                        "last_name": "Doe"
                                    },
                                    "member_count": 15,
                                    "is_private": False,
                                    "is_active": True,
                                    "max_members": 50,
                                    "user_role": "admin",
                                    "last_message": {
                                        "content": "Meeting tomorrow at 3 PM",
                                        "sender": "jane_smith",
                                        "created_at": "2024-01-01T10:00:00Z"
                                    },
                                    "unread_count": 2,
                                    "created_at": "2024-01-01T09:00:00Z"
                                }
                            ]
                        }
                    )
                ]
            ),
            201: OpenApiResponse(
                description="Group chat created successfully",
                examples=[
                    OpenApiExample(
                        "Group Created",
                        value={
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "New Study Group",
                            "description": "A group for studying together",
                            "creator": {
                                "id": 1,
                                "username": "john_doe"
                            },
                            "is_private": False,
                            "max_members": 25,
                            "member_count": 1,
                            "created_at": "2024-01-01T10:30:00Z"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Group Chats'],
        examples=[
            OpenApiExample(
                "Create Public Group",
                value={
                    "name": "Study Group - Advanced Math",
                    "description": "Group for discussing advanced mathematics topics",
                    "is_private": False,
                    "max_members": 30
                }
            ),
            OpenApiExample(
                "Create Private Group",
                value={
                    "name": "Close Friends",
                    "description": "Private group for close friends",
                    "is_private": True,
                    "max_members": 10
                }
            )
        ]
    )
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
    
    @extend_schema(
        description="Get, update, or delete a group chat. Only members can view, only admins/creator can modify.",
        responses={
            200: OpenApiResponse(
                description="Group chat retrieved/updated successfully",
                response=GroupChatSerializer
            ),
            204: OpenApiResponse(description="Group chat deleted successfully"),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not group member or insufficient privileges"),
            404: OpenApiResponse(description="Group chat not found")
        },
        tags=['Group Chats']
    )
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
    
    @extend_schema(
        description="Add a member to the group chat. Only group admins and creator can add members.",
        parameters=[
            OpenApiParameter(
                name='chat_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='UUID of the group chat'
            )
        ],
        request=AddMemberSerializer,
        responses={
            200: OpenApiResponse(
                description="Member added successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "message": "Added jane_smith to group chat",
                            "member": {
                                "user": {
                                    "id": 2,
                                    "username": "jane_smith",
                                    "first_name": "Jane",
                                    "last_name": "Smith"
                                },
                                "is_admin": False,
                                "joined_at": "2024-01-01T10:30:00Z"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Validation error or group is full"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not group admin"),
            404: OpenApiResponse(description="Group chat or user not found")
        },
        tags=['Group Management'],
        examples=[
            OpenApiExample(
                "Add Regular Member",
                value={
                    "user_id": 2,
                    "is_admin": False
                }
            ),
            OpenApiExample(
                "Add Admin Member",
                value={
                    "user_id": 3,
                    "is_admin": True
                }
            )
        ]
    )
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
    
    @extend_schema(
        description="Remove a member from the group chat. Only group admins and creator can remove members.",
        parameters=[
            OpenApiParameter(
                name='chat_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='UUID of the group chat'
            )
        ],
        request=RemoveMemberSerializer,
        responses={
            200: OpenApiResponse(
                description="Member removed successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "message": "Removed jane_smith from group chat"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not group admin"),
            404: OpenApiResponse(description="Group chat or user not found")
        },
        tags=['Group Management'],
        examples=[
            OpenApiExample(
                "Remove Member",
                value={
                    "user_id": 2
                }
            )
        ]
    )
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
    
    @extend_schema(
        description="Get messages from a group chat or send a new message. Automatically updates read status for the user.",
        parameters=[
            OpenApiParameter(
                name='chat_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='UUID of the group chat'
            ),
            OpenApiParameter(
                name='since',
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                description='Get messages since this timestamp (ISO format)',
                required=False
            )
        ],
        request=GroupMessageSerializer,
        responses={
            200: OpenApiResponse(
                description="Group messages retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "count": 25,
                            "results": [
                                {
                                    "id": "123e4567-e89b-12d3-a456-426614174000",
                                    "sender": {
                                        "id": 1,
                                        "username": "john_doe",
                                        "first_name": "John",
                                        "last_name": "Doe"
                                    },
                                    "content": "Welcome everyone to our study group!",
                                    "created_at": "2024-01-01T10:00:00Z",
                                    "updated_at": "2024-01-01T10:00:00Z",
                                    "attachments": []
                                }
                            ]
                        }
                    )
                ]
            ),
            201: OpenApiResponse(
                description="Message sent successfully",
                response=GroupMessageSerializer
            ),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not group member"),
            404: OpenApiResponse(description="Group chat not found")
        },
        tags=['Group Messages'],
        examples=[
            OpenApiExample(
                "Send Text Message",
                value={
                    "content": "Hello everyone! How's the project going?"
                }
            ),
            OpenApiExample(
                "Send Message with Mentions",
                value={
                    "content": "Hey @john_doe, can you share those notes we discussed?"
                }
            )
        ]
    )
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
    
    @extend_schema(
        description="Get, update, or delete a specific group message. Only group members can access, only sender can modify.",
        responses={
            200: OpenApiResponse(
                description="Group message retrieved/updated successfully",
                response=GroupMessageSerializer
            ),
            204: OpenApiResponse(description="Group message deleted successfully"),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not group member or sender"),
            404: OpenApiResponse(description="Group message not found")
        },
        tags=['Group Messages']
    )
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
    
    @extend_schema(
        description="Get notifications for the authenticated user with filtering and pagination support",
        parameters=[
            OpenApiParameter(
                name='type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by notification type: message, group_message, group_invite, mention, like, comment, etc.',
                required=False,
                enum=['message', 'group_message', 'group_invite', 'mention', 'like', 'comment', 'share', 'follow', 'system']
            ),
            OpenApiParameter(
                name='unread_only',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Show only unread notifications',
                required=False
            ),
            OpenApiParameter(
                name='since',
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                description='Get notifications since this timestamp',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Notifications retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "count": 10,
                            "results": [
                                {
                                    "id": "123e4567-e89b-12d3-a456-426614174000",
                                    "type": "message",
                                    "title": "New Message",
                                    "content": "john_doe sent you a message",
                                    "actor": {
                                        "id": 1,
                                        "username": "john_doe",
                                        "first_name": "John",
                                        "last_name": "Doe"
                                    },
                                    "is_read": False,
                                    "read_at": None,
                                    "created_at": "2024-01-01T10:30:00Z",
                                    "target_url": "/api/v1/messaging/messages/msg-123/"
                                }
                            ]
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Notifications']
    )
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
    
    @extend_schema(
        description="Get comprehensive unread counts for messages, notifications, and group chats for real-time UI updates",
        responses={
            200: OpenApiResponse(
                description="Unread counts retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "data": {
                                "unread_messages": 5,
                                "unread_notifications": 3,
                                "group_unread": {
                                    "123e4567-e89b-12d3-a456-426614174000": 2,
                                    "456e7890-e89b-12d3-a456-426614174001": 7
                                },
                                "total_unread": 17,
                                "breakdown": {
                                    "direct_messages": 5,
                                    "group_messages": 9,
                                    "notifications": 3
                                }
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Messaging Utilities']
    )
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


@extend_schema(
    description="Search for users to start conversations or add to groups. Supports fuzzy search across username, name, and email.",
    parameters=[
        OpenApiParameter(
            name='q',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Search query (minimum 2 characters)',
            required=True
        ),
        OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Maximum number of results (default: 10, max: 50)',
            required=False
        ),
        OpenApiParameter(
            name='exclude_groups',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Comma-separated group IDs to exclude users who are already members',
            required=False
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Users found successfully",
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "success": True,
                        "data": [
                            {
                                "id": 2,
                                "username": "jane_smith",
                                "first_name": "Jane",
                                "last_name": "Smith",
                                "profile_picture": "/media/profiles/jane.jpg",
                                "is_online": True,
                                "last_seen": "2024-01-01T10:25:00Z",
                                "mutual_connections": 5
                            }
                        ]
                    }
                )
            ]
        ),
        400: OpenApiResponse(description="Search query too short or invalid"),
        401: OpenApiResponse(description="Authentication required")
    },
    tags=['Messaging Utilities']
)
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


@extend_schema(
    description="Join a public group chat. Private groups require invitation from admins.",
    parameters=[
        OpenApiParameter(
            name='chat_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the group chat to join'
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Successfully joined group chat",
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "success": True,
                        "message": "Successfully joined CS Study Group",
                        "member": {
                            "user": {
                                "id": 1,
                                "username": "john_doe"
                            },
                            "is_admin": False,
                            "joined_at": "2024-01-01T10:30:00Z"
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Cannot join group (private, full, or already member)",
            examples=[
                OpenApiExample(
                    "Private Group",
                    value={
                        "success": False,
                        "error": "This is a private group chat"
                    }
                ),
                OpenApiExample(
                    "Group Full",
                    value={
                        "success": False,
                        "error": "Group chat is full"
                    }
                )
            ]
        ),
        401: OpenApiResponse(description="Authentication required"),
        404: OpenApiResponse(description="Group chat not found")
    },
    tags=['Group Management']
)
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
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Validation error occurred while joining group chat", exc_info=True)
        return Response({
            'success': False,
            'error': 'Invalid input data'
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    description="Leave a group chat. Users can leave any group they are members of.",
    parameters=[
        OpenApiParameter(
            name='chat_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the group chat to leave'
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Successfully left group chat",
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "success": True,
                        "message": "Successfully left CS Study Group"
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Not a member of this group",
            examples=[
                OpenApiExample(
                    "Not Member",
                    value={
                        "success": False,
                        "error": "You are not a member of this group"
                    }
                )
            ]
        ),
        401: OpenApiResponse(description="Authentication required"),
        404: OpenApiResponse(description="Group chat not found")
    },
    tags=['Group Management']
)
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
