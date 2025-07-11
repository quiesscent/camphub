from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from ..models import Post, UserInteraction
from users.models import Institution, Campus, UserProfile
from academic.models import Course
from unittest.mock import patch, MagicMock

User = get_user_model()

class PostFeedViewTest(TestCase):
    def setUp(self):
        # Create test data
        self.institution = Institution.objects.create(name="Test University", domain="test.edu")
        self.campus = Campus.objects.create(institution=self.institution, name="Main Campus")
        
        self.user1 = User.objects.create_user(email="user1@test.edu", username="user1", password="password", first_name="Test", last_name="User1")
        self.user_profile1 = UserProfile.objects.create(user=self.user1, institution=self.institution, campus=self.campus)
        
        self.user2 = User.objects.create_user(email="user2@test.edu", username="user2", password="password", first_name="Test", last_name="User2")
        self.user_profile2 = UserProfile.objects.create(user=self.user2, institution=self.institution, campus=self.campus)

        self.course = Course.objects.create(institution=self.institution, name="Test Course", code="CS101")
        self.user_profile1.user.enrolled_courses.add(self.course)

        # Create posts
        self.public_post = Post.objects.create(author=self.user2, content="A public post for everyone", visibility='public', location=self.campus)
        self.course_post = Post.objects.create(author=self.user2, content="A post for my course", visibility='private', course=self.course, location=self.campus)
        self.campus_post = Post.objects.create(author=self.user2, content="A post for my campus", visibility='private', location=self.campus)
        self.private_post = Post.objects.create(author=self.user2, content="A private post", visibility='private')

        self.client.login(email="user1@test.edu", password="password")

    def test_feed_authentication_required(self):
        self.client.logout()
        response = self.client.get(reverse('post-feed'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_feed_returns_correct_posts(self):
        response = self.client.get(reverse('post-feed'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        post_ids = [post['id'] for post in response.data['data']['posts']]
        
        self.assertIn(self.public_post.id, post_ids)
        self.assertIn(self.course_post.id, post_ids)
        self.assertIn(self.campus_post.id, post_ids)
        self.assertNotIn(self.private_post.id, post_ids)

    @patch('content.views.FeedAlgorithm')
    def test_feed_algorithm_is_called(self, MockFeedAlgorithm):
        # Mock the algorithm to verify it's being used
        mock_instance = MockFeedAlgorithm.return_value
        mock_instance.rank_feed.return_value = [self.public_post, self.course_post]

        response = self.client.get(reverse('post-feed'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the algorithm was instantiated with the correct user
        MockFeedAlgorithm.assert_called_with(self.user1)
        # Check that rank_feed was called on the instance
        mock_instance.rank_feed.assert_called_once()

    def test_feed_pagination(self):
        # Create more posts to test pagination
        for i in range(25):
            Post.objects.create(author=self.user2, content=f"Post {i}", visibility='public', location=self.campus)
        
        response = self.client.get(reverse('post-feed'), {'page': 1, 'limit': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']
        
        self.assertEqual(len(data['posts']), 10)
        self.assertEqual(data['pagination']['page'], 1)
        self.assertEqual(data['pagination']['limit'], 10)
        self.assertTrue(data['pagination']['has_next'])

        response = self.client.get(reverse('post-feed'), {'page': 3, 'limit': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']

        # Total posts = 25 + 3 original posts = 28. Page 3 should have 8 posts.
        self.assertEqual(len(data['posts']), 8)
        self.assertEqual(data['pagination']['page'], 3)
        self.assertFalse(data['pagination']['has_next'])

    def test_view_interaction_is_logged(self):
        # Clear existing interactions for a clean test
        UserInteraction.objects.all().delete()

        response = self.client.get(reverse('post-feed'), {'limit': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        posts_in_feed = response.data['data']['posts']
        post_ids_in_feed = {p['id'] for p in posts_in_feed}

        # Check that view interactions were created for the posts in the feed
        interactions = UserInteraction.objects.filter(user=self.user1, interaction_type='view')
        self.assertEqual(interactions.count(), len(post_ids_in_feed))

        interacted_post_ids = {i.post.id for i in interactions}
        self.assertEqual(post_ids_in_feed, interacted_post_ids)
