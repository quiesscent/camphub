from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import Institution, UserProfile
from .models import Course, CourseEnrollment, StudyGroup, StudyGroupMember
import datetime

User = get_user_model()


class CourseModelTest(TestCase):
    """Test cases for Course model"""
    
    def setUp(self):
        self.institution = Institution.objects.create(
            name="Test University",
            domain="test.edu",
            address="123 Test St"
        )
        
        self.instructor = User.objects.create_user(
            username="instructor",
            email="instructor@test.edu",
            password="testpass123",
            first_name="John",
            last_name="Instructor"
        )
        
        UserProfile.objects.create(
            user=self.instructor,
            institution=self.institution,
            student_id="INSTR001",  # Add unique student_id
            role='faculty'
        )
    
    def test_course_creation(self):
        """Test basic course creation"""
        course = Course.objects.create(
            institution=self.institution,
            course_code="CS101",
            course_name="Introduction to Computer Science",
            semester="fall",
            year=2025,
            instructor=self.instructor,
            description="Basic computer science course"
        )
        
        self.assertEqual(course.course_code, "CS101")
        self.assertEqual(course.semester_display, "Fall 2025")
        self.assertTrue(course.is_active)
        self.assertEqual(str(course), "CS101 - Introduction to Computer Science (fall 2025)")
    
    def test_course_validation(self):
        """Test course validation rules"""
        # Test instructor from different institution
        other_institution = Institution.objects.create(
            name="Other University",
            domain="other.edu",
            address="456 Other St"
        )
        
        other_instructor = User.objects.create_user(
            username="other_instructor",
            email="other@other.edu",
            password="testpass123"
        )
        
        UserProfile.objects.create(
            user=other_instructor,
            institution=other_institution,
            student_id="OTHER001",  # Add unique student_id
            role='faculty'
        )
        
        course = Course(
            institution=self.institution,
            course_code="CS102",
            course_name="Test Course",
            semester="fall",
            year=2025,
            instructor=other_instructor
        )
        
        with self.assertRaises(ValidationError):
            course.full_clean()
    
    def test_course_enrollment_methods(self):
        """Test course enrollment-related methods"""
        course = Course.objects.create(
            institution=self.institution,
            course_code="CS101",
            course_name="Test Course",
            semester="fall",
            year=2025,
            instructor=self.instructor,
            max_enrollment=2
        )
        
        student1 = User.objects.create_user(
            username="student1",
            email="student1@test.edu",
            password="testpass123"
        )
        
        UserProfile.objects.create(
            user=student1,
            institution=self.institution,
            student_id="STU001",  # Add unique student_id
            role='student'
        )
        
        # Test can_enroll
        self.assertTrue(course.can_enroll(student1))
        
        # Enroll student
        CourseEnrollment.objects.create(
            user=student1,
            course=course,
            role='student'
        )
        
        # Test enrollment count
        self.assertEqual(course.get_enrollment_count(), 1)
        
        # Test can't enroll twice
        self.assertFalse(course.can_enroll(student1))


class StudyGroupModelTest(TestCase):
    """Test cases for StudyGroup model"""
    
    def setUp(self):
        self.institution = Institution.objects.create(
            name="Test University",
            domain="test.edu",
            address="123 Test St"
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.edu",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        
        UserProfile.objects.create(
            user=self.user,
            institution=self.institution,
            student_id="USR001",  # Add unique student_id
            role='student'
        )
        
        self.instructor = User.objects.create_user(
            username="instructor",
            email="instructor@test.edu",
            password="testpass123"
        )
        
        UserProfile.objects.create(
            user=self.instructor,
            institution=self.institution,
            student_id="INSTR001",  # Add unique student_id
            role='faculty'
        )
        
        self.course = Course.objects.create(
            institution=self.institution,
            course_code="CS101",
            course_name="Test Course",
            semester="fall",
            year=2025,
            instructor=self.instructor
        )
        
        CourseEnrollment.objects.create(
            user=self.user,
            course=self.course,
            role='student'
        )
    
    def test_study_group_creation(self):
        """Test study group creation"""
        study_group = StudyGroup.objects.create(
            name="CS101 Study Group",
            description="Study group for CS101",
            course=self.course,
            creator=self.user,
            max_members=5
        )
        
        self.assertEqual(study_group.name, "CS101 Study Group")
        self.assertEqual(study_group.get_member_count(), 1)  # Creator is auto-added
        self.assertTrue(study_group.is_moderator(self.user))
    
    def test_study_group_membership(self):
        """Test study group membership management"""
        study_group = StudyGroup.objects.create(
            name="Test Group",
            description="Test description",
            creator=self.user,
            max_members=3
        )
        
        # Create another user
        user2 = User.objects.create_user(
            username="user2",
            email="user2@test.edu",
            password="testpass123"
        )
        
        UserProfile.objects.create(
            user=user2,
            institution=self.institution,
            student_id="USR002",  # Add unique student_id
            role='student'
        )
        
        # Test can join
        self.assertTrue(study_group.can_join(user2))
        
        # Add member
        StudyGroupMember.objects.create(
            group=study_group,
            user=user2,
            role='member'
        )
        
        # Test member count
        self.assertEqual(study_group.get_member_count(), 2)
        
        # Test can't join when full
        user3 = User.objects.create_user(
            username="user3",
            email="user3@test.edu",
            password="testpass123"
        )
        
        UserProfile.objects.create(
            user=user3,
            institution=self.institution,
            student_id="USR003",  # Add unique student_id
            role='student'
        )
        
        StudyGroupMember.objects.create(
            group=study_group,
            user=user3,
            role='member'
        )
        
        # Now group is full
        user4 = User.objects.create_user(
            username="user4",
            email="user4@test.edu",
            password="testpass123"
        )
        
        UserProfile.objects.create(
            user=user4,
            institution=self.institution,
            student_id="USR004",  # Add unique student_id
            role='student'
        )
        
        self.assertFalse(study_group.can_join(user4))


class CourseAPITest(APITestCase):
    """Test cases for Course API endpoints"""
    
    def setUp(self):
        self.institution = Institution.objects.create(
            name="Test University",
            domain="test.edu",
            address="123 Test St"
        )
        
        self.student = User.objects.create_user(
            username="student",
            email="student@test.edu",
            password="testpass123",
            first_name="Test",
            last_name="Student"
        )
        
        UserProfile.objects.create(
            user=self.student,
            institution=self.institution,
            student_id="STU001",  # Add unique student_id
            role='student'
        )
        
        self.instructor = User.objects.create_user(
            username="instructor",
            email="instructor@test.edu",
            password="testpass123",
            first_name="Test",
            last_name="Instructor"
        )
        
        UserProfile.objects.create(
            user=self.instructor,
            institution=self.institution,
            student_id="INSTR001",  # Add unique student_id
            role='faculty'
        )
        
        self.course = Course.objects.create(
            institution=self.institution,
            course_code="CS101",
            course_name="Introduction to Computer Science",
            semester="fall",
            year=2025,
            instructor=self.instructor,
            description="Basic computer science course"
        )
    
    def get_tokens_for_user(self, user):
        """Helper method to get JWT tokens for user"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    
    def test_course_list_api(self):
        """Test course list API endpoint"""
        tokens = self.get_tokens_for_user(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        response = self.client.get('/api/v1/academic/courses/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['course_code'], 'CS101')
    
    def test_course_detail_api(self):
        """Test course detail API endpoint"""
        tokens = self.get_tokens_for_user(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        response = self.client.get(f'/api/v1/academic/courses/{self.course.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['course_code'], 'CS101')
        self.assertFalse(data['data']['is_enrolled'])
    
    def test_course_enrollment_api(self):
        """Test course enrollment API endpoint"""
        tokens = self.get_tokens_for_user(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        response = self.client.post(f'/api/v1/academic/courses/{self.course.id}/enroll/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify enrollment was created
        enrollment = CourseEnrollment.objects.get(user=self.student, course=self.course)
        self.assertEqual(enrollment.role, 'student')
    
    def test_course_creation_api(self):
        """Test course creation API endpoint"""
        tokens = self.get_tokens_for_user(self.instructor)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        course_data = {
            'course_code': 'CS102',
            'course_name': 'Advanced Computer Science',
            'semester': 'spring',
            'year': 2025,
            'instructor_id': self.instructor.id,
            'institution_id': self.institution.id,
            'description': 'Advanced CS course',
            'max_enrollment': 30
        }
        
        response = self.client.post('/api/v1/academic/courses/create/', course_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['course_code'], 'CS102')
    
    def test_unauthorized_course_creation(self):
        """Test that students cannot create courses"""
        tokens = self.get_tokens_for_user(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        course_data = {
            'course_code': 'CS103',
            'course_name': 'Test Course',
            'semester': 'fall',
            'year': 2025,
            'instructor_id': self.instructor.id,
            'institution_id': self.institution.id
        }
        
        response = self.client.post('/api/v1/academic/courses/create/', course_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class StudyGroupAPITest(APITestCase):
    """Test cases for StudyGroup API endpoints"""
    
    def setUp(self):
        self.institution = Institution.objects.create(
            name="Test University",
            domain="test.edu",
            address="123 Test St"
        )
        
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@test.edu",
            password="testpass123",
            first_name="User",
            last_name="One"
        )
        
        UserProfile.objects.create(
            user=self.user1,
            institution=self.institution,
            student_id="USR001",  # Add unique student_id
            role='student'
        )
        
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@test.edu",
            password="testpass123",
            first_name="User",
            last_name="Two"
        )
        
        UserProfile.objects.create(
            user=self.user2,
            institution=self.institution,
            student_id="USR002",  # Add unique student_id
            role='student'
        )
        
        self.instructor = User.objects.create_user(
            username="instructor",
            email="instructor@test.edu",
            password="testpass123"
        )
        
        UserProfile.objects.create(
            user=self.instructor,
            institution=self.institution,
            student_id="INSTR001",  # Add unique student_id
            role='faculty'
        )
        
        self.course = Course.objects.create(
            institution=self.institution,
            course_code="CS101",
            course_name="Test Course",
            semester="fall",
            year=2025,
            instructor=self.instructor
        )
        
        # Enroll users in course
        CourseEnrollment.objects.create(user=self.user1, course=self.course, role='student')
        CourseEnrollment.objects.create(user=self.user2, course=self.course, role='student')
        
        self.study_group = StudyGroup.objects.create(
            name="Test Study Group",
            description="A test study group",
            course=self.course,
            creator=self.user1,
            max_members=5
        )
    
    def get_tokens_for_user(self, user):
        """Helper method to get JWT tokens for user"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    
    def test_study_group_list_api(self):
        """Test study group list API endpoint"""
        tokens = self.get_tokens_for_user(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        response = self.client.get('/api/v1/academic/study-groups/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['name'], 'Test Study Group')
    
    def test_study_group_detail_api(self):
        """Test study group detail API endpoint"""
        tokens = self.get_tokens_for_user(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        response = self.client.get(f'/api/v1/academic/study-groups/{self.study_group.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], 'Test Study Group')
        self.assertTrue(data['data']['is_member'])
        self.assertTrue(data['data']['is_moderator'])
    
    def test_study_group_creation_api(self):
        """Test study group creation API endpoint"""
        tokens = self.get_tokens_for_user(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        group_data = {
            'name': 'New Study Group',
            'description': 'A new study group',
            'course_id': self.course.id,
            'max_members': 10,
            'is_private': False,
            'meeting_location': 'Library',
            'meeting_frequency': 'weekly'
        }
        
        response = self.client.post('/api/v1/academic/study-groups/create/', group_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], 'New Study Group')
    
    def test_join_study_group_api(self):
        """Test joining a study group via API"""
        tokens = self.get_tokens_for_user(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        response = self.client.post(f'/api/v1/academic/study-groups/{self.study_group.id}/join/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify membership was created
        membership = StudyGroupMember.objects.get(group=self.study_group, user=self.user2)
        self.assertEqual(membership.role, 'member')
    
    def test_leave_study_group_api(self):
        """Test leaving a study group via API"""
        # First join the group
        StudyGroupMember.objects.create(
            group=self.study_group,
            user=self.user2,
            role='member'
        )
        
        tokens = self.get_tokens_for_user(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        response = self.client.post(f'/api/v1/academic/study-groups/{self.study_group.id}/leave/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify membership was deactivated
        membership = StudyGroupMember.objects.get(group=self.study_group, user=self.user2)
        self.assertFalse(membership.is_active)
    
    def test_academic_dashboard_api(self):
        """Test academic dashboard API endpoint"""
        tokens = self.get_tokens_for_user(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        response = self.client.get('/api/v1/academic/dashboard/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check that dashboard data structure is correct
        self.assertIn('courses', data['data'])
        self.assertIn('study_groups', data['data'])
        self.assertIn('recent_courses', data['data'])
        self.assertIn('recent_study_groups', data['data'])
        self.assertIn('upcoming_meetings', data['data'])
        
        # Check course stats
        course_stats = data['data']['courses']
        self.assertIn('total_courses', course_stats)
        self.assertIn('enrolled_courses', course_stats)
        
        # Check study group stats
        sg_stats = data['data']['study_groups']
        self.assertIn('total_groups', sg_stats)
        self.assertIn('user_groups', sg_stats)


class FormTest(TestCase):
    """Test cases for academic forms"""
    
    def setUp(self):
        self.institution = Institution.objects.create(
            name="Test University",
            domain="test.edu",
            address="123 Test St"
        )
        
        self.instructor = User.objects.create_user(
            username="instructor",
            email="instructor@test.edu",
            password="testpass123"
        )
        
        UserProfile.objects.create(
            user=self.instructor,
            institution=self.institution,
            student_id="INSTR001",  # Add unique student_id
            role='faculty'
        )
    
    def test_course_form_validation(self):
        """Test course form validation"""
        from .serializers import CourseCreateSerializer
        
        form_data = {
            'institution_id': self.institution.id,
            'course_code': 'cs101',  # Should be converted to uppercase
            'course_name': 'Test Course',
            'semester': 'fall',
            'year': 2025,
            'instructor_id': self.instructor.id,
            'description': 'Test description',
            'max_enrollment': 30,
            'enrollment_open': True,
            'is_active': True
        }
        
        serializer = CourseCreateSerializer(data=form_data)
        self.assertTrue(serializer.is_valid())
        
        # Test that course code is converted to uppercase
        course = serializer.save()
        self.assertEqual(course.course_code, 'CS101')
    
    def test_study_group_form_validation(self):
        """Test study group form validation"""
        from .serializers import StudyGroupCreateSerializer
        
        user = User.objects.create_user(
            username="student",
            email="student@test.edu",
            password="testpass123"
        )
        
        UserProfile.objects.create(
            user=user,
            institution=self.institution,
            student_id="STU001",  # Add unique student_id
            role='student'
        )
        
        course = Course.objects.create(
            institution=self.institution,
            course_code="CS101",
            course_name="Test Course",
            semester="fall",
            year=2025,
            instructor=self.instructor
        )
        
        # Enroll user in course
        CourseEnrollment.objects.create(user=user, course=course, role='student')
        
        form_data = {
            'name': 'Test Study Group',
            'description': 'Test description',
            'course_id': course.id,
            'max_members': 10,
            'is_private': False,
            'meeting_location': 'Library',
            'meeting_frequency': 'weekly'
        }
        
        # Create a mock request with user
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/')
        request.user = user
        
        serializer = StudyGroupCreateSerializer(data=form_data, context={'request': request})
        self.assertTrue(serializer.is_valid())
