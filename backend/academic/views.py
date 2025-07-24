from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.openapi import OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular import openapi
from users.views import api_response
from .models import Course, CourseEnrollment, StudyGroup, StudyGroupMember
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, CourseCreateSerializer,
    CourseEnrollmentSerializer, EnrollInCourseSerializer, BulkEnrollmentSerializer,
    StudyGroupListSerializer, StudyGroupDetailSerializer, StudyGroupCreateSerializer,
    StudyGroupMemberSerializer, JoinStudyGroupSerializer,
    AcademicDashboardSerializer, CourseStatsSerializer, StudyGroupStatsSerializer,
    CourseSearchSerializer, StudyGroupSearchSerializer
)

User = get_user_model()


@extend_schema_view(
    get=extend_schema(
        operation_id='list_courses',
        summary='List all courses',
        description='''
        Retrieve a paginated list of courses with filtering and search capabilities.
        Users can filter by semester, year, instructor, and search by course code or name.
        Only shows courses from user's institution if they have a profile.
        ''',
        parameters=[
            OpenApiParameter(
                name='search',
                description='Search term for filtering courses by code, name, or instructor',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='semester',
                description='Filter by academic semester',
                required=False,
                type=str,
                enum=['fall', 'spring', 'summer', 'winter'],
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='year',
                description='Filter by academic year',
                required=False,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='instructor',
                description='Filter by instructor ID',
                required=False,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='enrollment_open',
                description='Filter by enrollment status',
                required=False,
                type=bool,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='my_courses',
                description='Show only courses user is enrolled in',
                required=False,
                type=bool,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=CourseListSerializer(many=True),
                description='Successfully retrieved courses',
                examples=[
                    OpenApiExample(
                        'Success Response',
                        value={
                            'success': True,
                            'data': [
                                {
                                    'id': 1,
                                    'course_code': 'CS101',
                                    'course_name': 'Introduction to Computer Science',
                                    'semester': 'fall',
                                    'year': 2024,
                                    'instructor_name': 'Dr. John Smith',
                                    'enrollment_count': 25,
                                    'study_groups_count': 3,
                                    'is_enrolled': False
                                }
                            ],
                            'message': 'Courses retrieved successfully'
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description='Authentication required'),
        },
        tags=['Academic - Courses']
    )
)
class CourseListView(generics.ListAPIView):
    """List courses with filtering and search capabilities"""
    serializer_class = CourseListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Course.objects.select_related(
            'institution', 'instructor'
        ).prefetch_related(
            'enrollments'
        ).annotate(
            enrollment_count=Count('enrollments', filter=Q(enrollments__is_active=True)),
            study_groups_count=Count('study_groups', filter=Q(study_groups__is_active=True))
        )
        
        # Filter by user's institution if they have a profile
        if hasattr(user, 'profile'):
            queryset = queryset.filter(institution=user.profile.institution)
        
        # Apply search and filters
        search_query = self.request.query_params.get('search', '')
        semester = self.request.query_params.get('semester', '')
        year = self.request.query_params.get('year', '')
        instructor_id = self.request.query_params.get('instructor', '')
        enrollment_open = self.request.query_params.get('enrollment_open', '')
        my_courses = self.request.query_params.get('my_courses', '').lower() == 'true'
        
        if search_query:
            queryset = queryset.filter(
                Q(course_code__icontains=search_query) |
                Q(course_name__icontains=search_query) |
                Q(instructor__first_name__icontains=search_query) |
                Q(instructor__last_name__icontains=search_query)
            )
        
        if semester:
            queryset = queryset.filter(semester=semester)
        
        if year:
            queryset = queryset.filter(year=year)
        
        if instructor_id:
            queryset = queryset.filter(instructor_id=instructor_id)
        
        if enrollment_open:
            queryset = queryset.filter(enrollment_open=enrollment_open.lower() == 'true')
        
        if my_courses:
            queryset = queryset.filter(
                enrollments__user=user,
                enrollments__is_active=True
            )
        
        return queryset.filter(is_active=True).order_by('-year', 'semester', 'course_code')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, serializer.data, "Courses retrieved successfully")


@extend_schema_view(
    get=extend_schema(
        operation_id='get_course_detail',
        summary='Get course details',
        description='''
        Retrieve detailed information about a specific course including enrollment count,
        study groups, and user's enrollment status.
        ''',
        responses={
            200: OpenApiResponse(
                response=CourseDetailSerializer,
                description='Successfully retrieved course details',
                examples=[
                    OpenApiExample(
                        'Success Response',
                        value={
                            'success': True,
                            'data': {
                                'id': 1,
                                'course_code': 'CS101',
                                'course_name': 'Introduction to Computer Science',
                                'description': 'Basic computer science concepts',
                                'semester': 'fall',
                                'year': 2024,
                                'instructor': {
                                    'id': 1,
                                    'name': 'Dr. John Smith',
                                    'email': 'john.smith@university.edu'
                                },
                                'enrollment_count': 25,
                                'max_enrollment': 50,
                                'is_enrolled': False,
                                'enrollment_open': True
                            },
                            'message': 'Course details retrieved successfully'
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Course not found'),
        },
        tags=['Academic - Courses']
    )
)
class CourseDetailView(generics.RetrieveAPIView):
    """Retrieve detailed course information"""
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Course.objects.select_related(
            'institution', 'instructor'
        ).prefetch_related(
            'enrollments__user',
            'study_groups'
        ).annotate(
            enrollment_count=Count('enrollments', filter=Q(enrollments__is_active=True)),
            study_groups_count=Count('study_groups', filter=Q(study_groups__is_active=True))
        )
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, serializer.data, "Course details retrieved successfully")


@extend_schema_view(
    post=extend_schema(
        operation_id='create_course',
        summary='Create a new course',
        description='''
        Create a new course. Only faculty and staff members can create courses.
        The course will be automatically assigned to the user's institution.
        ''',
        request=CourseCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=CourseDetailSerializer,
                description='Course created successfully',
                examples=[
                    OpenApiExample(
                        'Success Response',
                        value={
                            'success': True,
                            'data': {
                                'id': 1,
                                'course_code': 'CS101',
                                'course_name': 'Introduction to Computer Science',
                                'semester': 'fall',
                                'year': 2024,
                                'instructor_id': 1,
                                'institution_id': 1
                            },
                            'message': 'Course created successfully'
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description='Validation error',
                examples=[
                    OpenApiExample(
                        'Validation Error',
                        value={
                            'success': False,
                            'errors': {
                                'course_code': ['This field is required.'],
                                'course_name': ['Ensure this field has at most 200 characters.']
                            },
                            'message': 'Course creation failed'
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description='Authentication required'),
            403: OpenApiResponse(
                description='Permission denied - only faculty and staff can create courses',
                examples=[
                    OpenApiExample(
                        'Permission Denied',
                        value={
                            'success': False,
                            'message': 'Only faculty and staff can create courses'
                        }
                    )
                ]
            ),
        },
        tags=['Academic - Courses']
    )
)
class CourseCreateView(generics.CreateAPIView):
    """Create new courses (faculty/staff only)"""
    serializer_class = CourseCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Set institution from user's profile if not provided
        if hasattr(self.request.user, 'profile'):
            serializer.save(institution=self.request.user.profile.institution)
    
    def create(self, request, *args, **kwargs):
        # Check if user can create courses
        if not hasattr(request.user, 'profile') or request.user.profile.role not in ['faculty', 'staff']:
            return api_response(
                False, None, "Only faculty and staff can create courses", 
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            course = serializer.save()
            return api_response(
                True, 
                CourseDetailSerializer(course, context={'request': request}).data,
                "Course created successfully",
                status_code=status.HTTP_201_CREATED
            )
        
        return api_response(
            False, None, "Course creation failed", 
            serializer.errors, status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    operation_id='enroll_in_course',
    summary='Enroll in a course',
    description='''
    Enroll the authenticated user in a specific course.
    Users cannot enroll in the same course twice.
    ''',
    request=EnrollInCourseSerializer,
    responses={
        200: OpenApiResponse(
            response=CourseEnrollmentSerializer,
            description='Successfully enrolled in course',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'data': {
                            'id': 1,
                            'user_id': 1,
                            'course_id': 1,
                            'role': 'student',
                            'enrollment_date': '2024-01-15T10:30:00Z'
                        },
                        'message': 'Successfully enrolled in course'
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description='Bad request - already enrolled or course full',
            examples=[
                OpenApiExample(
                    'Already Enrolled',
                    value={
                        'success': False,
                        'message': 'Already enrolled in this course'
                    }
                )
            ]
        ),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Course not found'),
    },
    tags=['Academic - Enrollments']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def enroll_in_course(request, course_id):
    """Enroll user in a course"""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    serializer = EnrollInCourseSerializer(
        data={'course_id': course_id}, 
        context={'request': request}
    )
    
    if serializer.is_valid():
        # Check if already enrolled
        existing = CourseEnrollment.objects.filter(
            course=course, user=request.user, is_active=True
        ).first()
        
        if existing:
            return api_response(
                False, None, "Already enrolled in this course",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create enrollment
        enrollment = CourseEnrollment.objects.create(
            course=course,
            user=request.user,
            role='student'
        )
        
        return api_response(
            True,
            CourseEnrollmentSerializer(enrollment, context={'request': request}).data,
            "Successfully enrolled in course"
        )
    
    return api_response(
        False, None, "Enrollment failed", 
        serializer.errors, status.HTTP_400_BAD_REQUEST
    )


@extend_schema(
    operation_id='unenroll_from_course',
    summary='Unenroll from a course',
    description='''
    Remove the authenticated user's enrollment from a specific course.
    Instructors cannot unenroll from their own courses.
    ''',
    responses={
        200: OpenApiResponse(
            description='Successfully unenrolled from course',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'message': 'Successfully unenrolled from course'
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description='Bad request - instructors cannot unenroll',
            examples=[
                OpenApiExample(
                    'Instructor Error',
                    value={
                        'success': False,
                        'message': 'Instructors cannot unenroll from their own courses'
                    }
                )
            ]
        ),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Course or enrollment not found'),
    },
    tags=['Academic - Enrollments']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def unenroll_from_course(request, course_id):
    """Unenroll user from a course"""
    course = get_object_or_404(Course, id=course_id)
    
    enrollment = get_object_or_404(
        CourseEnrollment,
        course=course,
        user=request.user,
        is_active=True
    )
    
    # Prevent instructors from unenrolling themselves
    if enrollment.role == 'instructor':
        return api_response(
            False, None, "Instructors cannot unenroll from their own courses",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    enrollment.is_active = False
    enrollment.save()
    
    return api_response(True, None, "Successfully unenrolled from course")


@extend_schema_view(
    get=extend_schema(
        operation_id='list_course_enrollments',
        summary='List course enrollments',
        description='''
        List all enrollments for a specific course.
        Only instructors and TAs can view course enrollments.
        ''',
        responses={
            200: OpenApiResponse(
                response=CourseEnrollmentSerializer(many=True),
                description='Successfully retrieved enrollments',
                examples=[
                    OpenApiExample(
                        'Success Response',
                        value={
                            'success': True,
                            'data': [
                                {
                                    'id': 1,
                                    'user': {
                                        'id': 1,
                                        'name': 'John Doe',
                                        'email': 'john@university.edu'
                                    },
                                    'role': 'student',
                                    'enrollment_date': '2024-01-15T10:30:00Z'
                                }
                            ],
                            'message': 'Enrollments retrieved successfully'
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description='Authentication required'),
            403: OpenApiResponse(description='Permission denied - instructors/TAs only'),
            404: OpenApiResponse(description='Course not found'),
        },
        tags=['Academic - Enrollments']
    )
)
class CourseEnrollmentsView(generics.ListAPIView):
    """List enrollments for a course (instructors/TAs only)"""
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, id=course_id)
        
        # Check if user has permission to view enrollments
        user_enrollment = course.enrollments.filter(
            user=self.request.user, is_active=True
        ).first()
        
        if not user_enrollment or user_enrollment.role not in ['instructor', 'ta']:
            return CourseEnrollment.objects.none()
        
        return CourseEnrollment.objects.filter(
            course=course, is_active=True
        ).select_related('user', 'course').order_by('enrollment_date')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists() and queryset.model == CourseEnrollment:
            return api_response(
                False, None, "Permission denied or course not found",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, serializer.data, "Enrollments retrieved successfully")


@extend_schema_view(
    get=extend_schema(
        operation_id='list_study_groups',
        summary='List study groups',
        description='''
        Retrieve a paginated list of study groups with filtering capabilities.
        Users can filter by course, privacy level, and search by name or description.
        ''',
        parameters=[
            OpenApiParameter(
                name='search',
                description='Search term for filtering groups by name or description',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='course',
                description='Filter by course ID',
                required=False,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='is_private',
                description='Filter by privacy level',
                required=False,
                type=bool,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='meeting_frequency',
                description='Filter by meeting frequency',
                required=False,
                type=str,
                enum=['weekly', 'biweekly', 'monthly', 'irregular'],
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='my_groups',
                description='Show only groups user is a member of',
                required=False,
                type=bool,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=StudyGroupListSerializer(many=True),
                description='Successfully retrieved study groups',
            ),
            401: OpenApiResponse(description='Authentication required'),
        },
        tags=['Academic - Study Groups']
    )
)
class StudyGroupListView(generics.ListAPIView):
    """List study groups with filtering capabilities"""
    serializer_class = StudyGroupListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = StudyGroup.objects.select_related(
            'creator', 'course', 'course__institution'
        ).prefetch_related(
            'members'
        ).annotate(
            member_count=Count('members', filter=Q(members__is_active=True))
        )
        
        # Filter by user's institution courses or general groups
        if hasattr(user, 'profile'):
            queryset = queryset.filter(
                Q(course__institution=user.profile.institution) |
                Q(course__isnull=True)
            )
        
        # Apply search and filters
        search_query = self.request.query_params.get('search', '')
        course_id = self.request.query_params.get('course', '')
        is_private = self.request.query_params.get('is_private', '')
        meeting_frequency = self.request.query_params.get('meeting_frequency', '')
        my_groups = self.request.query_params.get('my_groups', '').lower() == 'true'
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        if is_private:
            queryset = queryset.filter(is_private=is_private.lower() == 'true')
        
        if meeting_frequency:
            queryset = queryset.filter(meeting_frequency=meeting_frequency)
        
        if my_groups:
            queryset = queryset.filter(
                members__user=user,
                members__is_active=True
            )
        
        return queryset.filter(is_active=True).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, serializer.data, "Study groups retrieved successfully")


@extend_schema_view(
    get=extend_schema(
        operation_id='get_study_group_detail',
        summary='Get study group details',
        description='''
        Retrieve detailed information about a specific study group.
        Private groups can only be viewed by members.
        ''',
        responses={
            200: OpenApiResponse(
                response=StudyGroupDetailSerializer,
                description='Successfully retrieved study group details',
            ),
            401: OpenApiResponse(description='Authentication required'),
            403: OpenApiResponse(description='Access denied to private study group'),
            404: OpenApiResponse(description='Study group not found'),
        },
        tags=['Academic - Study Groups']
    )
)
class StudyGroupDetailView(generics.RetrieveAPIView):
    """Retrieve detailed study group information"""
    serializer_class = StudyGroupDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return StudyGroup.objects.select_related(
            'creator', 'course'
        ).prefetch_related(
            'members__user'
        ).annotate(
            member_count=Count('members', filter=Q(members__is_active=True))
        )
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if user can view private group
        if instance.is_private:
            is_member = instance.members.filter(user=request.user, is_active=True).exists()
            if not is_member:
                return api_response(
                    False, None, "Access denied to private study group",
                    status_code=status.HTTP_403_FORBIDDEN
                )
        
        serializer = self.get_serializer(instance)
        return api_response(True, serializer.data, "Study group details retrieved successfully")


@extend_schema_view(
    post=extend_schema(
        operation_id='create_study_group',
        summary='Create a new study group',
        description='''
        Create a new study group. The creator automatically becomes a moderator.
        If associated with a course, the user must be enrolled in that course.
        ''',
        request=StudyGroupCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=StudyGroupDetailSerializer,
                description='Study group created successfully',
            ),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
        },
        tags=['Academic - Study Groups']
    )
)
class StudyGroupCreateView(generics.CreateAPIView):
    """Create new study groups"""
    serializer_class = StudyGroupCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            study_group = serializer.save()
            return api_response(
                True,
                StudyGroupDetailSerializer(study_group, context={'request': request}).data,
                "Study group created successfully",
                status_code=status.HTTP_201_CREATED
            )
        
        return api_response(
            False, None, "Study group creation failed",
            serializer.errors, status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    operation_id='join_study_group',
    summary='Join a study group',
    description='''
    Join a study group as a member. Users cannot join the same group twice.
    Private groups may require approval (future feature).
    ''',
    request=JoinStudyGroupSerializer,
    responses={
        200: OpenApiResponse(
            response=StudyGroupMemberSerializer,
            description='Successfully joined study group',
        ),
        400: OpenApiResponse(description='Already a member or group is full'),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Study group not found'),
    },
    tags=['Academic - Study Groups']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def join_study_group(request, group_id):
    """Join a study group"""
    study_group = get_object_or_404(StudyGroup, id=group_id, is_active=True)
    
    serializer = JoinStudyGroupSerializer(
        data=request.data,
        context={'request': request, 'study_group': study_group}
    )
    
    if serializer.is_valid():
        # Check if already a member
        existing = StudyGroupMember.objects.filter(
            group=study_group, user=request.user, is_active=True
        ).first()
        
        if existing:
            return api_response(
                False, None, "Already a member of this study group",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create membership
        membership = StudyGroupMember.objects.create(
            group=study_group,
            user=request.user,
            role='member'
        )
        
        return api_response(
            True,
            StudyGroupMemberSerializer(membership, context={'request': request}).data,
            "Successfully joined study group"
        )
    
    return api_response(
        False, None, "Failed to join study group",
        serializer.errors, status.HTTP_400_BAD_REQUEST
    )


@extend_schema(
    operation_id='leave_study_group',
    summary='Leave a study group',
    description='''
    Leave a study group. Group creators cannot leave if they are the only moderator.
    They must promote another member to moderator first.
    ''',
    responses={
        200: OpenApiResponse(
            description='Successfully left study group',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'message': 'Successfully left study group'
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description='Cannot leave - only moderator remaining',
            examples=[
                OpenApiExample(
                    'Only Moderator Error',
                    value={
                        'success': False,
                        'message': 'Cannot leave group as the only moderator. Promote another member first.'
                    }
                )
            ]
        ),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Study group or membership not found'),
    },
    tags=['Academic - Study Groups']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def leave_study_group(request, group_id):
    """Leave a study group"""
    study_group = get_object_or_404(StudyGroup, id=group_id)
    
    membership = get_object_or_404(
        StudyGroupMember,
        group=study_group,
        user=request.user,
        is_active=True
    )
    
    # Prevent creator from leaving if they're the only moderator
    if study_group.creator == request.user:
        other_moderators = StudyGroupMember.objects.filter(
            group=study_group,
            role='moderator',
            is_active=True
        ).exclude(user=request.user)
        
        if not other_moderators.exists():
            return api_response(
                False, None, "Cannot leave group as the only moderator. Promote another member first.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    membership.is_active = False
    membership.save()
    
    return api_response(True, None, "Successfully left study group")


@extend_schema_view(
    get=extend_schema(
        operation_id='list_study_group_members',
        summary='List study group members',
        description='''
        List all members of a study group.
        Private groups can only be viewed by members.
        ''',
        responses={
            200: OpenApiResponse(
                response=StudyGroupMemberSerializer(many=True),
                description='Successfully retrieved study group members',
            ),
            401: OpenApiResponse(description='Authentication required'),
            403: OpenApiResponse(description='Access denied or study group not found'),
        },
        tags=['Academic - Study Groups']
    )
)
class StudyGroupMembersView(generics.ListAPIView):
    """List members of a study group"""
    serializer_class = StudyGroupMemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        group_id = self.kwargs['group_id']
        study_group = get_object_or_404(StudyGroup, id=group_id, is_active=True)
        
        # Check if user can view members (must be member or public group)
        if study_group.is_private:
            is_member = study_group.members.filter(user=self.request.user, is_active=True).exists()
            if not is_member:
                return StudyGroupMember.objects.none()
        
        return StudyGroupMember.objects.filter(
            group=study_group, is_active=True
        ).select_related('user').order_by('role', 'joined_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists() and queryset.model == StudyGroupMember:
            return api_response(
                False, None, "Access denied or study group not found",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, serializer.data, "Study group members retrieved successfully")


@extend_schema_view(
    get=extend_schema(
        operation_id='list_course_study_groups',
        summary='List study groups for a course',
        description='''
        List all study groups associated with a specific course.
        User must be enrolled in the course to view its study groups.
        ''',
        responses={
            200: OpenApiResponse(
                response=StudyGroupListSerializer(many=True),
                description='Successfully retrieved course study groups',
            ),
            401: OpenApiResponse(description='Authentication required'),
            403: OpenApiResponse(description='Course not found or access denied'),
        },
        tags=['Academic - Study Groups']
    )
)
class CourseStudyGroupsView(generics.ListAPIView):
    """List study groups for a specific course"""
    serializer_class = StudyGroupListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, id=course_id, is_active=True)
        
        # Check if user is enrolled in the course
        if not course.enrollments.filter(user=self.request.user, is_active=True).exists():
            return StudyGroup.objects.none()
        
        return StudyGroup.objects.filter(
            course=course, is_active=True
        ).select_related(
            'creator', 'course'
        ).annotate(
            member_count=Count('members', filter=Q(members__is_active=True))
        ).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists() and queryset.model == StudyGroup:
            return api_response(
                False, None, "Course not found or access denied",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, serializer.data, "Course study groups retrieved successfully")


@extend_schema(
    operation_id='get_academic_dashboard',
    summary='Get academic dashboard data',
    description='''
    Retrieve comprehensive academic dashboard data including:
    - Course statistics (enrolled, teaching, total)
    - Study group statistics (member of, moderating)
    - Recent courses and study groups
    - Upcoming meetings and deadlines
    ''',
    responses={
        200: OpenApiResponse(
            response=AcademicDashboardSerializer,
            description='Successfully retrieved dashboard data',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'data': {
                            'courses': {
                                'total_courses': 45,
                                'enrolled_courses': 4,
                                'teaching_courses': 0,
                                'current_semester_courses': 4
                            },
                            'study_groups': {
                                'total_groups': 23,
                                'user_groups': 2,
                                'user_moderated_groups': 1
                            },
                            'recent_courses': [],
                            'recent_study_groups': [],
                            'upcoming_meetings': []
                        },
                        'message': 'Dashboard data retrieved successfully'
                    }
                )
            ]
        ),
        401: OpenApiResponse(description='Authentication required'),
    },
    tags=['Academic - Dashboard']
)
class AcademicDashboardView(APIView):
    """Academic dashboard with statistics and recent items"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Course statistics
        if hasattr(user, 'profile'):
            institution = user.profile.institution
            all_courses = Course.objects.filter(institution=institution, is_active=True)
        else:
            all_courses = Course.objects.filter(is_active=True)
        
        enrolled_courses = all_courses.filter(
            enrollments__user=user, enrollments__is_active=True
        )
        
        teaching_courses = all_courses.filter(
            enrollments__user=user, 
            enrollments__role__in=['instructor', 'ta'],
            enrollments__is_active=True
        )
        
        current_year = timezone.now().year
        current_semester_courses = enrolled_courses.filter(year=current_year)
        
        course_stats = {
            'total_courses': all_courses.count(),
            'active_courses': all_courses.count(),
            'enrolled_courses': enrolled_courses.count(),
            'teaching_courses': teaching_courses.count(),
            'current_semester_courses': current_semester_courses.count(),
            'total_students': all_courses.aggregate(
                total=Count('enrollments', filter=Q(enrollments__is_active=True))
            )['total'] or 0
        }
        
        # Study group statistics
        if hasattr(user, 'profile'):
            all_groups = StudyGroup.objects.filter(
                Q(course__institution=user.profile.institution) |
                Q(course__isnull=True),
                is_active=True
            )
        else:
            all_groups = StudyGroup.objects.filter(is_active=True)
        
        user_groups = all_groups.filter(
            members__user=user, members__is_active=True
        )
        
        user_moderated_groups = all_groups.filter(
            members__user=user, 
            members__role='moderator',
            members__is_active=True
        )
        
        study_group_stats = {
            'total_groups': all_groups.count(),
            'public_groups': all_groups.filter(is_private=False).count(),
            'private_groups': all_groups.filter(is_private=True).count(),
            'course_groups': all_groups.filter(course__isnull=False).count(),
            'general_groups': all_groups.filter(course__isnull=True).count(),
            'user_groups': user_groups.count(),
            'user_moderated_groups': user_moderated_groups.count()
        }
        
        # Recent items
        recent_courses = enrolled_courses.order_by('-created_at')[:5]
        recent_study_groups = user_groups.order_by('-created_at')[:5]
        
        # Upcoming meetings
        upcoming_meetings = StudyGroup.objects.filter(
            members__user=user,
            members__is_active=True,
            meeting_time__gte=timezone.now(),
            is_active=True
        ).order_by('meeting_time')[:5]
        
        upcoming_meetings_data = []
        for group in upcoming_meetings:
            upcoming_meetings_data.append({
                'id': group.id,
                'name': group.name,
                'meeting_time': group.meeting_time,
                'meeting_location': group.meeting_location,
                'course': group.course.course_code if group.course else None
            })
        
        dashboard_data = {
            'courses': course_stats,
            'study_groups': study_group_stats,
            'recent_courses': CourseListSerializer(
                recent_courses, many=True, context={'request': request}
            ).data,
            'recent_study_groups': StudyGroupListSerializer(
                recent_study_groups, many=True, context={'request': request}
            ).data,
            'upcoming_meetings': upcoming_meetings_data
        }
        
        return api_response(True, dashboard_data, "Dashboard data retrieved successfully")
