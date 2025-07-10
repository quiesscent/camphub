from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json
import uuid

from .models import (
    DirectMessage, 
    GroupChat, 
    GroupChatMember, 
    GroupMessage, 
    Notification,
    MessageAttachment
)
from .utils import (
    validate_message_content,
    extract_mentions,
    get_user_online_status,
    generate_conversation_id,
    validate_group_chat_name
)

User = get_user_model()


class BaseMessagingTestCase(APITestCase):
    """Base test case with common setup for messaging tests"""
    
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        
        # Set up API client with authentication
        self.client = APIClient()
        self.authenticate_user(self.user1)
    
    def authenticate_user(self, user):
        """Authenticate a user for API requests"""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def create_test_message(self, sender, recipient, content="Test message"):
        """Helper method to create a test message"""
        return DirectMessage.objects.create(
            sender=sender,
            recipient=recipient,
            content=content
        )
    
    def create_test_group_chat(self, creator, name="Test Group"):
        """Helper method to create a test group chat"""
        return GroupChat.objects.create(
            creator=creator,
            name=name,
            description="Test group description"
        )


class DirectMessageModelTestCase(BaseMessagingTestCase):
    """Test cases for DirectMessage model"""
    
    def test_create_direct_message(self):
        """Test creating a direct message"""
        message = self.create_test_message(self.user1, self.user2)
        
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.recipient, self.user2)
        self.assertEqual(message.content, "Test message")
        self.assertFalse(message.is_read)
        self.assertIsNone(message.read_at)
    
    def test_cannot_send_message_to_self(self):
        """Test that users cannot send messages to themselves"""
        with self.assertRaises(ValidationError):
            DirectMessage.objects.create(
                sender=self.user1,
                recipient=self.user1,
                content="Test message"
            )
    
    def test_mark_message_as_read(self):
        """Test marking a message as read"""
        message = self.create_test_message(self.user1, self.user2)
        
        self.assertFalse(message.is_read)
        message.mark_as_read()
        
        self.assertTrue(message.is_read)
        self.assertIsNotNone(message.read_at)
    
    def test_get_conversation_messages(self):
        """Test getting messages between two users"""
        # Create messages in both directions
        msg1 = self.create_test_message(self.user1, self.user2, "Message 1")
        msg2 = self.create_test_message(self.user2, self.user1, "Message 2")
        msg3 = self.create_test_message(self.user1, self.user3, "Message 3")
        
        conversation = DirectMessage.get_conversation_messages(self.user1, self.user2)
        
        self.assertEqual(conversation.count(), 2)
        self.assertIn(msg1, conversation)
        self.assertIn(msg2, conversation)
        self.assertNotIn(msg3, conversation)
    
    def test_get_unread_count(self):
        """Test getting unread message count"""
        # Create some messages
        self.create_test_message(self.user1, self.user2)
        self.create_test_message(self.user1, self.user2)
        msg3 = self.create_test_message(self.user1, self.user2)
        
        # Mark one as read
        msg3.mark_as_read()
        
        unread_count = DirectMessage.get_unread_count(self.user2)
        self.assertEqual(unread_count, 2)
    
    def test_get_user_conversations(self):
        """Test getting user conversations"""
        # Create messages with different users
        self.create_test_message(self.user1, self.user2)
        self.create_test_message(self.user1, self.user3)
        
        conversations = DirectMessage.get_user_conversations(self.user1)
        
        self.assertEqual(len(conversations), 2)
        other_user_ids = [conv['other_user_id'] for conv in conversations]
        self.assertIn(self.user2.id, other_user_ids)
        self.assertIn(self.user3.id, other_user_ids)


class GroupChatModelTestCase(BaseMessagingTestCase):
    """Test cases for GroupChat model"""
    
    def test_create_group_chat(self):
        """Test creating a group chat"""
        group = self.create_test_group_chat(self.user1)
        
        self.assertEqual(group.creator, self.user1)
        self.assertEqual(group.name, "Test Group")
        self.assertTrue(group.is_active)
        self.assertFalse(group.is_private)
        self.assertEqual(group.max_members, 100)
    
    def test_group_chat_validation(self):
        """Test group chat validation"""
        # Test minimum member limit
        with self.assertRaises(ValidationError):
            GroupChat.objects.create(
                creator=self.user1,
                name="Test Group",
                max_members=1
            )
        
        # Test minimum name length
        with self.assertRaises(ValidationError):
            GroupChat.objects.create(
                creator=self.user1,
                name="A"
            )
    
    def test_add_member(self):
        """Test adding a member to group chat"""
        group = self.create_test_group_chat(self.user1)
        member = group.add_member(self.user2)
        
        self.assertTrue(group.is_member(self.user2))
        self.assertFalse(group.is_admin(self.user2))
        self.assertEqual(member.user, self.user2)
    
    def test_add_admin_member(self):
        """Test adding an admin member to group chat"""
        group = self.create_test_group_chat(self.user1)
        member = group.add_member(self.user2, is_admin=True)
        
        self.assertTrue(group.is_member(self.user2))
        self.assertTrue(group.is_admin(self.user2))
    
    def test_remove_member(self):
        """Test removing a member from group chat"""
        group = self.create_test_group_chat(self.user1)
        group.add_member(self.user2)
        
        self.assertTrue(group.is_member(self.user2))
        
        group.remove_member(self.user2)
        
        self.assertFalse(group.is_member(self.user2))
    
    def test_member_count(self):
        """Test getting member count"""
        group = self.create_test_group_chat(self.user1)
        
        # Initially 0 members (creator needs to be added separately)
        self.assertEqual(group.get_member_count(), 0)
        
        group.add_member(self.user1, is_admin=True)
        group.add_member(self.user2)
        
        self.assertEqual(group.get_member_count(), 2)
    
    def test_can_add_members(self):
        """Test checking if members can be added"""
        group = GroupChat.objects.create(
            creator=self.user1,
            name="Small Group",
            max_members=2
        )
        
        self.assertTrue(group.can_add_members())
        
        group.add_member(self.user1)
        self.assertTrue(group.can_add_members())
        
        group.add_member(self.user2)
        self.assertFalse(group.can_add_members())


class GroupMessageModelTestCase(BaseMessagingTestCase):
    """Test cases for GroupMessage model"""
    
    def test_create_group_message(self):
        """Test creating a group message"""
        group = self.create_test_group_chat(self.user1)
        group.add_member(self.user1, is_admin=True)
        
        message = GroupMessage.objects.create(
            chat=group,
            sender=self.user1,
            content="Test group message"
        )
        
        self.assertEqual(message.chat, group)
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.content, "Test group message")
    
    def test_cannot_send_message_if_not_member(self):
        """Test that non-members cannot send messages"""
        group = self.create_test_group_chat(self.user1)
        
        with self.assertRaises(ValidationError):
            GroupMessage.objects.create(
                chat=group,
                sender=self.user2,  # Not a member
                content="Test message"
            )


class NotificationModelTestCase(BaseMessagingTestCase):
    """Test cases for Notification model"""
    
    def test_create_message_notification(self):
        """Test creating a message notification"""
        message = self.create_test_message(self.user1, self.user2)
        
        notification = Notification.create_message_notification(
            sender=self.user1,
            recipient=self.user2,
            message=message
        )
        
        self.assertEqual(notification.user, self.user2)
        self.assertEqual(notification.type, 'message')
        self.assertEqual(notification.actor, self.user1)
        self.assertEqual(notification.target_object, message)
        self.assertFalse(notification.is_read)
    
    def test_mark_notification_as_read(self):
        """Test marking a notification as read"""
        message = self.create_test_message(self.user1, self.user2)
        notification = Notification.create_message_notification(
            sender=self.user1,
            recipient=self.user2,
            message=message
        )
        
        self.assertFalse(notification.is_read)
        notification.mark_as_read()
        
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
    def test_get_unread_count(self):
        """Test getting unread notification count"""
        message1 = self.create_test_message(self.user1, self.user2)
        message2 = self.create_test_message(self.user1, self.user2)
        
        Notification.create_message_notification(self.user1, self.user2, message1)
        notification2 = Notification.create_message_notification(self.user1, self.user2, message2)
        
        self.assertEqual(Notification.get_unread_count(self.user2), 2)
        
        notification2.mark_as_read()
        self.assertEqual(Notification.get_unread_count(self.user2), 1)
    
    def test_mark_all_as_read(self):
        """Test marking all notifications as read"""
        message1 = self.create_test_message(self.user1, self.user2)
        message2 = self.create_test_message(self.user1, self.user2)
        
        Notification.create_message_notification(self.user1, self.user2, message1)
        Notification.create_message_notification(self.user1, self.user2, message2)
        
        count = Notification.mark_all_as_read(self.user2)
        
        self.assertEqual(count, 2)
        self.assertEqual(Notification.get_unread_count(self.user2), 0)


class DirectMessageAPITestCase(BaseMessagingTestCase):
    """Test cases for DirectMessage API endpoints"""
    
    def test_send_direct_message(self):
        """Test sending a direct message via API"""
        url = reverse('messaging:direct-message-list')
        data = {
            'recipient_id': self.user2.id,
            'content': 'Test API message'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DirectMessage.objects.count(), 1)
        
        message = DirectMessage.objects.first()
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.recipient, self.user2)
        self.assertEqual(message.content, 'Test API message')
    
    def test_list_direct_messages(self):
        """Test listing direct messages"""
        self.create_test_message(self.user1, self.user2)
        self.create_test_message(self.user2, self.user1)
        
        url = reverse('messaging:direct-message-list')
        response = self.client.get(url, {'other_user': self.user2.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_cannot_send_message_to_self(self):
        """Test that API prevents sending messages to self"""
        url = reverse('messaging:direct-message-list')
        data = {
            'recipient_id': self.user1.id,
            'content': 'Test message to self'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_mark_message_as_read(self):
        """Test marking messages as read via API"""
        message = self.create_test_message(self.user2, self.user1)
        
        url = reverse('messaging:mark-message-read')
        data = {
            'message_ids': [str(message.id)]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message.refresh_from_db()
        self.assertTrue(message.is_read)
    
    def test_conversation_list(self):
        """Test getting conversation list"""
        self.create_test_message(self.user1, self.user2)
        self.create_test_message(self.user1, self.user3)
        
        url = reverse('messaging:conversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)


class GroupChatAPITestCase(BaseMessagingTestCase):
    """Test cases for GroupChat API endpoints"""
    
    def test_create_group_chat(self):
        """Test creating a group chat via API"""
        url = reverse('messaging:group-chat-list')
        data = {
            'name': 'API Test Group',
            'description': 'Created via API',
            'is_private': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GroupChat.objects.count(), 1)
        
        group = GroupChat.objects.first()
        self.assertEqual(group.creator, self.user1)
        self.assertEqual(group.name, 'API Test Group')
    
    def test_list_group_chats(self):
        """Test listing group chats"""
        group = self.create_test_group_chat(self.user1)
        group.add_member(self.user1, is_admin=True)
        
        url = reverse('messaging:group-chat-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_add_member_to_group(self):
        """Test adding a member to group chat"""
        group = self.create_test_group_chat(self.user1)
        group.add_member(self.user1, is_admin=True)
        
        url = reverse('messaging:group-chat-members', kwargs={'chat_id': group.id})
        data = {
            'user_id': self.user2.id,
            'is_admin': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(group.is_member(self.user2))
    
    def test_send_group_message(self):
        """Test sending a group message"""
        group = self.create_test_group_chat(self.user1)
        group.add_member(self.user1, is_admin=True)
        
        url = reverse('messaging:group-chat-messages', kwargs={'chat_id': group.id})
        data = {
            'content': 'Test group message'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GroupMessage.objects.count(), 1)
        
        message = GroupMessage.objects.first()
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.chat, group)
    
    def test_join_public_group(self):
        """Test joining a public group chat"""
        group = self.create_test_group_chat(self.user2)  # Created by user2
        
        url = reverse('messaging:join-group-chat', kwargs={'chat_id': group.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(group.is_member(self.user1))
    
    def test_cannot_join_private_group(self):
        """Test that users cannot join private groups directly"""
        group = GroupChat.objects.create(
            creator=self.user2,
            name="Private Group",
            is_private=True
        )
        
        url = reverse('messaging:join-group-chat', kwargs={'chat_id': group.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_leave_group_chat(self):
        """Test leaving a group chat"""
        group = self.create_test_group_chat(self.user2)
        group.add_member(self.user1)
        
        url = reverse('messaging:leave-group-chat', kwargs={'chat_id': group.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(group.is_member(self.user1))


class NotificationAPITestCase(BaseMessagingTestCase):
    """Test cases for Notification API endpoints"""
    
    def test_list_notifications(self):
        """Test listing notifications"""
        message = self.create_test_message(self.user2, self.user1)
        Notification.create_message_notification(self.user2, self.user1, message)
        
        url = reverse('messaging:notification-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_mark_notification_as_read(self):
        """Test marking a notification as read"""
        message = self.create_test_message(self.user2, self.user1)
        notification = Notification.create_message_notification(self.user2, self.user1, message)
        
        url = reverse('messaging:mark-notification-read', kwargs={'notification_id': notification.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
    
    def test_mark_all_notifications_as_read(self):
        """Test marking all notifications as read"""
        message1 = self.create_test_message(self.user2, self.user1)
        message2 = self.create_test_message(self.user2, self.user1)
        
        Notification.create_message_notification(self.user2, self.user1, message1)
        Notification.create_message_notification(self.user2, self.user1, message2)
        
        url = reverse('messaging:mark-all-notifications-read')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.get_unread_count(self.user1), 0)
    
    def test_get_unread_count(self):
        """Test getting unread counts"""
        message = self.create_test_message(self.user2, self.user1)
        Notification.create_message_notification(self.user2, self.user1, message)
        
        url = reverse('messaging:unread-count')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['unread_messages'], 1)
        self.assertEqual(response.data['data']['unread_notifications'], 1)


class UtilsTestCase(BaseMessagingTestCase):
    """Test cases for utility functions"""
    
    def test_validate_message_content(self):
        """Test message content validation"""
        # Valid content
        valid_content = validate_message_content("Hello world!")
        self.assertEqual(valid_content, "Hello world!")
        
        # Empty content
        with self.assertRaises(ValidationError):
            validate_message_content("")
        
        # Too long content
        with self.assertRaises(ValidationError):
            validate_message_content("x" * 5001)
    
    def test_extract_mentions(self):
        """Test extracting mentions from content"""
        content = "Hello @user1 and @user2, how are you?"
        mentions = extract_mentions(content)
        
        self.assertEqual(len(mentions), 2)
        self.assertIn('user1', mentions)
        self.assertIn('user2', mentions)
    
    def test_generate_conversation_id(self):
        """Test generating conversation ID"""
        conv_id1 = generate_conversation_id(self.user1, self.user2)
        conv_id2 = generate_conversation_id(self.user2, self.user1)
        
        # Should be the same regardless of order
        self.assertEqual(conv_id1, conv_id2)
    
    def test_validate_group_chat_name(self):
        """Test group chat name validation"""
        # Valid name
        valid_name = validate_group_chat_name("Test Group")
        self.assertEqual(valid_name, "Test Group")
        
        # Too short
        with self.assertRaises(ValidationError):
            validate_group_chat_name("A")
        
        # Too long
        with self.assertRaises(ValidationError):
            validate_group_chat_name("x" * 101)
        
        # Invalid characters
        with self.assertRaises(ValidationError):
            validate_group_chat_name("Test<Group>")


class PermissionTestCase(BaseMessagingTestCase):
    """Test cases for permissions"""
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access endpoints"""
        self.client.credentials()  # Remove authentication
        
        url = reverse('messaging:direct-message-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_cannot_access_others_messages(self):
        """Test that users cannot access messages they're not part of"""
        message = self.create_test_message(self.user2, self.user3)
        
        url = reverse('messaging:direct-message-detail', kwargs={'pk': message.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cannot_manage_others_group_chats(self):
        """Test that users cannot manage group chats they don't own"""
        group = self.create_test_group_chat(self.user2)
        
        url = reverse('messaging:group-chat-members', kwargs={'chat_id': group.id})
        data = {'user_id': self.user3.id}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cannot_access_others_notifications(self):
        """Test that users cannot access others' notifications"""
        message = self.create_test_message(self.user2, self.user3)
        notification = Notification.create_message_notification(self.user2, self.user3, message)
        
        url = reverse('messaging:notification-detail', kwargs={'pk': notification.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SearchTestCase(BaseMessagingTestCase):
    """Test cases for search functionality"""
    
    def test_search_users(self):
        """Test searching for users"""
        url = reverse('messaging:search-users')
        response = self.client.get(url, {'q': 'user'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)  # user2 and user3
    
    def test_search_users_minimum_length(self):
        """Test that search query must be at least 2 characters"""
        url = reverse('messaging:search-users')
        response = self.client.get(url, {'q': 'u'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_search_excludes_self(self):
        """Test that search excludes the current user"""
        url = reverse('messaging:search-users')
        response = self.client.get(url, {'q': 'user1'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 0)  # Should not include self
