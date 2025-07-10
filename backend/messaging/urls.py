from django.urls import path, include
from . import views

app_name = 'messaging'

urlpatterns = [
    # Direct Messages
    path('messages/', views.DirectMessageListCreateView.as_view(), name='direct-message-list'),
    path('messages/<uuid:pk>/', views.DirectMessageDetailView.as_view(), name='direct-message-detail'),
    path('messages/mark-read/', views.MarkMessageAsReadView.as_view(), name='mark-message-read'),
    
    # Conversations
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    
    # Group Chats
    path('group-chats/', views.GroupChatListCreateView.as_view(), name='group-chat-list'),
    path('group-chats/<uuid:pk>/', views.GroupChatDetailView.as_view(), name='group-chat-detail'),
    path('group-chats/<uuid:chat_id>/members/', views.GroupChatMemberView.as_view(), name='group-chat-members'),
    path('group-chats/<uuid:chat_id>/messages/', views.GroupChatMessagesView.as_view(), name='group-chat-messages'),
    path('group-chats/<uuid:chat_id>/join/', views.join_group_chat, name='join-group-chat'),
    path('group-chats/<uuid:chat_id>/leave/', views.leave_group_chat, name='leave-group-chat'),
    
    # Group Messages
    path('group-messages/<uuid:pk>/', views.GroupMessageDetailView.as_view(), name='group-message-detail'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<uuid:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/<uuid:notification_id>/mark-read/', views.MarkNotificationAsReadView.as_view(), name='mark-notification-read'),
    path('notifications/mark-all-read/', views.MarkAllNotificationsAsReadView.as_view(), name='mark-all-notifications-read'),
    
    # Utility endpoints
    path('unread-count/', views.UnreadCountView.as_view(), name='unread-count'),
    path('search/users/', views.search_users, name='search-users'),
]