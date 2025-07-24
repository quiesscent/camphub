from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Course, CourseEnrollment, StudyGroup, StudyGroupMember

User = get_user_model()


class InstructorSerializer(serializers.ModelSerializer):
    """Serializer for instructor information in course details"""
    name = serializers.SerializerMethodField(
        help_text="Full name of the instructor"
    )
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name']
        
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for course list view with essential information"""
    instructor_name = serializers.SerializerMethodField(
        help_text="Full name of the course instructor"
    )
    enrollment_count = serializers.IntegerField(
        read_only=True,
        help_text="Current number of enrolled students"
    )
    study_groups_count = serializers.IntegerField(
        read_only=True,
        help_text="Number of active study groups for this course"
    )
    semester_display = serializers.CharField(
        read_only=True,
        help_text="Formatted semester and year display (e.g., 'Fall 2024')"
    )
    is_enrolled = serializers.SerializerMethodField(
        help_text="Whether the current user is enrolled in this course"
    )
    
    class Meta:
        model = Course
        fields = [
            'id', 'course_code', 'course_name', 'semester', 'year',
            'semester_display', 'instructor_name', 'enrollment_count',
            'study_groups_count', 'enrollment_open', 'is_enrolled',
            'max_enrollment', 'created_at'
        ]
        
    def get_instructor_name(self, obj):
        return f"{obj.instructor.first_name} {obj.instructor.last_name}".strip()
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.enrollments.filter(user=request.user, is_active=True).exists()


class CourseDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed course information"""
    instructor = InstructorSerializer(
        read_only=True,
        help_text="Detailed instructor information"
    )
    enrollment_count = serializers.IntegerField(
        read_only=True,
        help_text="Current number of enrolled students"
    )
    study_groups_count = serializers.IntegerField(
        read_only=True,
        help_text="Number of active study groups for this course"
    )
    semester_display = serializers.CharField(
        read_only=True,
        help_text="Formatted semester and year display"
    )
    is_enrolled = serializers.SerializerMethodField(
        help_text="Whether the current user is enrolled in this course"
    )
    is_enrollment_full = serializers.BooleanField(
        read_only=True,
        help_text="Whether the course has reached maximum enrollment"
    )
    can_enroll = serializers.SerializerMethodField(
        help_text="Whether the current user can enroll in this course"
    )
    institution_name = serializers.CharField(
        source='institution.name',
        read_only=True,
        help_text="Name of the institution offering this course"
    )
    
    class Meta:
        model = Course
        fields = [
            'id', 'institution_name', 'course_code', 'course_name',
            'description', 'semester', 'year', 'semester_display',
            'instructor', 'max_enrollment', 'enrollment_count',
            'study_groups_count', 'enrollment_open', 'is_active',
            'is_enrolled', 'is_enrollment_full', 'can_enroll',
            'created_at', 'updated_at'
        ]
        
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.enrollments.filter(user=request.user, is_active=True).exists()
    
    def get_can_enroll(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.can_enroll(request.user)


class CourseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new courses"""
    course_code = serializers.CharField(
        max_length=20,
        required=True,
        help_text="Unique course code (e.g., 'CS101', 'MATH201'). Will be converted to uppercase.",
        error_messages={
            'required': 'Course code is required',
            'max_length': 'Course code cannot exceed 20 characters',
            'blank': 'Course code cannot be blank'
        }
    )
    course_name = serializers.CharField(
        max_length=200,
        required=True,
        help_text="Full descriptive name of the course",
        error_messages={
            'required': 'Course name is required',
            'max_length': 'Course name cannot exceed 200 characters',
            'blank': 'Course name cannot be blank'
        }
    )
    semester = serializers.ChoiceField(
        choices=Course.SEMESTER_CHOICES,
        required=True,
        help_text="Academic semester when the course is offered",
        error_messages={
            'required': 'Semester is required',
            'invalid_choice': 'Please select a valid semester'
        }
    )
    year = serializers.IntegerField(
        required=True,
        min_value=2020,
        max_value=2030,
        help_text="Academic year (between 2020 and 2030)",
        error_messages={
            'required': 'Academic year is required',
            'min_value': 'Year must be 2020 or later',
            'max_value': 'Year cannot exceed 2030'
        }
    )
    instructor_id = serializers.IntegerField(
        write_only=True,
        required=False,
        help_text="ID of the instructor. Defaults to current user if not specified.",
        error_messages={
            'invalid': 'Please provide a valid instructor ID'
        }
    )
    institution_id = serializers.IntegerField(
        write_only=True,
        required=False,
        help_text="ID of the institution. Defaults to user's institution if not specified.",
        error_messages={
            'invalid': 'Please provide a valid institution ID'
        }
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Detailed course description and objectives"
    )
    max_enrollment = serializers.IntegerField(
        default=100,
        min_value=1,
        help_text="Maximum number of students that can enroll (minimum 1)",
        error_messages={
            'min_value': 'Maximum enrollment must be at least 1'
        }
    )
    enrollment_open = serializers.BooleanField(
        default=True,
        help_text="Whether enrollment is currently open for new students"
    )
    
    class Meta:
        model = Course
        fields = [
            'course_code', 'course_name', 'semester', 'year',
            'instructor_id', 'institution_id', 'description',
            'max_enrollment', 'enrollment_open'
        ]
        
    def validate_course_code(self, value):
        """Convert course code to uppercase and validate uniqueness"""
        value = value.upper().strip()
        
        # Check for uniqueness within institution/semester/year
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile'):
            institution = request.user.profile.institution
            semester = self.initial_data.get('semester')
            year = self.initial_data.get('year')
            
            if semester and year:
                if Course.objects.filter(
                    institution=institution,
                    course_code=value,
                    semester=semester,
                    year=year
                ).exists():
                    raise serializers.ValidationError(
                        f"Course {value} already exists for {semester} {year}"
                    )
        
        return value
    
    def validate_year(self, value):
        """Ensure year is not in the past"""
        current_year = timezone.now().year
        if value < current_year:
            raise serializers.ValidationError(
                "Cannot create courses for past years"
            )
        return value
    
    def validate(self, attrs):
        """Validate instructor and institution"""
        request = self.context.get('request')
        
        # Set default instructor to current user
        if 'instructor_id' not in attrs and request:
            attrs['instructor_id'] = request.user.id
        
        # Set default institution to user's institution
        if 'institution_id' not in attrs and request and hasattr(request.user, 'profile'):
            attrs['institution_id'] = request.user.profile.institution.id
        
        return attrs
    
    def create(self, validated_data):
        """Create course with proper instructor and institution assignment"""
        instructor_id = validated_data.pop('instructor_id', None)
        institution_id = validated_data.pop('institution_id', None)
        
        if instructor_id:
            validated_data['instructor_id'] = instructor_id
        if institution_id:
            validated_data['institution_id'] = institution_id
            
        return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user information in enrollments"""
    name = serializers.SerializerMethodField(
        help_text="Full name of the user"
    )
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name']
        
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for course enrollment information"""
    user = UserSerializer(
        read_only=True,
        help_text="User enrolled in the course"
    )
    course_code = serializers.CharField(
        source='course.course_code',
        read_only=True,
        help_text="Course code"
    )
    course_name = serializers.CharField(
        source='course.course_name',
        read_only=True,
        help_text="Course name"
    )
    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True,
        help_text="Human-readable role name"
    )
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'user', 'course_code', 'course_name',
            'role', 'role_display', 'enrollment_date',
            'is_active', 'grade', 'completion_date'
        ]


class EnrollInCourseSerializer(serializers.Serializer):
    """Serializer for enrolling in a course"""
    course_id = serializers.IntegerField(
        required=True,
        help_text="ID of the course to enroll in",
        error_messages={
            'required': 'Course ID is required',
            'invalid': 'Please provide a valid course ID'
        }
    )
    
    def validate_course_id(self, value):
        """Validate that course exists and is available for enrollment"""
        try:
            course = Course.objects.get(id=value, is_active=True)
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found or inactive")
        
        request = self.context.get('request')
        if request and not course.can_enroll(request.user):
            if not course.enrollment_open:
                raise serializers.ValidationError("Enrollment is closed for this course")
            elif course.is_enrollment_full():
                raise serializers.ValidationError("Course enrollment is full")
            else:
                raise serializers.ValidationError("You cannot enroll in this course")
        
        return value


class BulkEnrollmentSerializer(serializers.Serializer):
    """Serializer for bulk enrollment operations"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="List of user IDs to enroll",
        error_messages={
            'required': 'User IDs list is required',
            'empty': 'At least one user ID must be provided'
        }
    )
    role = serializers.ChoiceField(
        choices=CourseEnrollment.ROLE_CHOICES,
        default='student',
        help_text="Role to assign to all enrolled users"
    )


class StudyGroupListSerializer(serializers.ModelSerializer):
    """Serializer for study group list view"""
    creator_name = serializers.SerializerMethodField(
        help_text="Full name of the group creator"
    )
    course_code = serializers.CharField(
        source='course.course_code',
        read_only=True,
        help_text="Associated course code (if any)"
    )
    member_count = serializers.IntegerField(
        read_only=True,
        help_text="Current number of active members"
    )
    is_member = serializers.SerializerMethodField(
        help_text="Whether the current user is a member of this group"
    )
    is_full = serializers.BooleanField(
        read_only=True,
        help_text="Whether the group has reached maximum capacity"
    )
    next_meeting = serializers.DateTimeField(
        read_only=True,
        help_text="Next scheduled meeting time"
    )
    
    class Meta:
        model = StudyGroup
        fields = [
            'id', 'name', 'description', 'course_code', 'creator_name',
            'max_members', 'member_count', 'is_private', 'is_full',
            'meeting_location', 'meeting_time', 'next_meeting',
            'meeting_frequency', 'is_member', 'created_at'
        ]
        
    def get_creator_name(self, obj):
        return f"{obj.creator.first_name} {obj.creator.last_name}".strip()
    
    def get_is_member(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.members.filter(user=request.user, is_active=True).exists()


class StudyGroupDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed study group information"""
    creator = UserSerializer(
        read_only=True,
        help_text="User who created this study group"
    )
    course = CourseListSerializer(
        read_only=True,
        help_text="Associated course information (if any)"
    )
    member_count = serializers.IntegerField(
        read_only=True,
        help_text="Current number of active members"
    )
    is_member = serializers.SerializerMethodField(
        help_text="Whether the current user is a member of this group"
    )
    is_moderator = serializers.SerializerMethodField(
        help_text="Whether the current user is a moderator of this group"
    )
    can_join = serializers.SerializerMethodField(
        help_text="Whether the current user can join this group"
    )
    is_full = serializers.BooleanField(
        read_only=True,
        help_text="Whether the group has reached maximum capacity"
    )
    next_meeting = serializers.DateTimeField(
        read_only=True,
        help_text="Next scheduled meeting time"
    )
    
    class Meta:
        model = StudyGroup
        fields = [
            'id', 'name', 'description', 'course', 'creator',
            'max_members', 'member_count', 'is_private', 'is_full',
            'meeting_location', 'meeting_time', 'next_meeting',
            'meeting_frequency', 'is_member', 'is_moderator',
            'can_join', 'is_active', 'created_at', 'updated_at'
        ]
        
    def get_is_member(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.members.filter(user=request.user, is_active=True).exists()
    
    def get_is_moderator(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.is_moderator(request.user)
    
    def get_can_join(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.can_join(request.user)


class StudyGroupCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new study groups"""
    name = serializers.CharField(
        max_length=200,
        required=True,
        help_text="Name of the study group (maximum 200 characters)",
        error_messages={
            'required': 'Study group name is required',
            'max_length': 'Name cannot exceed 200 characters',
            'blank': 'Name cannot be blank'
        }
    )
    description = serializers.CharField(
        required=True,
        help_text="Description of the study group's purpose and goals",
        error_messages={
            'required': 'Description is required',
            'blank': 'Description cannot be blank'
        }
    )
    course_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID of associated course (optional for general study groups)",
        error_messages={
            'invalid': 'Please provide a valid course ID'
        }
    )
    max_members = serializers.IntegerField(
        default=10,
        min_value=2,
        max_value=50,
        help_text="Maximum number of members (between 2 and 50)",
        error_messages={
            'min_value': 'Study group must allow at least 2 members',
            'max_value': 'Study group cannot exceed 50 members'
        }
    )
    is_private = serializers.BooleanField(
        default=False,
        help_text="Whether the group requires approval to join"
    )
    meeting_location = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text="Regular meeting location (optional)"
    )
    meeting_time = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Regular meeting time (optional)"
    )
    meeting_frequency = serializers.ChoiceField(
        choices=StudyGroup._meta.get_field('meeting_frequency').choices,
        default='weekly',
        help_text="How often the group meets"
    )
    
    class Meta:
        model = StudyGroup
        fields = [
            'name', 'description', 'course_id', 'max_members',
            'is_private', 'meeting_location', 'meeting_time',
            'meeting_frequency'
        ]
        
    def validate_course_id(self, value):
        """Validate that course exists and user is enrolled"""
        if value is None:
            return value
            
        try:
            course = Course.objects.get(id=value, is_active=True)
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found or inactive")
        
        # Check if user is enrolled in the course
        request = self.context.get('request')
        if request and not course.enrollments.filter(user=request.user, is_active=True).exists():
            raise serializers.ValidationError(
                "You must be enrolled in the course to create a study group for it"
            )
        
        return value
    
    def validate_meeting_time(self, value):
        """Ensure meeting time is not in the past"""
        if value and value < timezone.now():
            raise serializers.ValidationError("Meeting time cannot be in the past")
        return value
    
    def create(self, validated_data):
        """Create study group with proper course assignment"""
        course_id = validated_data.pop('course_id', None)
        request = self.context.get('request')
        
        validated_data['creator'] = request.user
        
        if course_id:
            validated_data['course_id'] = course_id
            
        return super().create(validated_data)


class StudyGroupMemberSerializer(serializers.ModelSerializer):
    """Serializer for study group member information"""
    user = UserSerializer(
        read_only=True,
        help_text="User who is a member of the group"
    )
    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True,
        help_text="Human-readable role name"
    )
    group_name = serializers.CharField(
        source='group.name',
        read_only=True,
        help_text="Name of the study group"
    )
    
    class Meta:
        model = StudyGroupMember
        fields = [
            'id', 'user', 'group_name', 'role', 'role_display',
            'joined_at', 'is_active', 'contributions', 'last_active'
        ]


class JoinStudyGroupSerializer(serializers.Serializer):
    """Serializer for joining a study group"""
    message = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Optional message when requesting to join (for private groups)"
    )
    
    def validate(self, attrs):
        """Validate that user can join the group"""
        study_group = self.context.get('study_group')
        request = self.context.get('request')
        
        if not study_group or not request:
            raise serializers.ValidationError("Invalid request context")
        
        if not study_group.can_join(request.user):
            if study_group.is_full():
                raise serializers.ValidationError("Study group is full")
            elif study_group.members.filter(user=request.user, is_active=True).exists():
                raise serializers.ValidationError("Already a member of this group")
            else:
                raise serializers.ValidationError("Cannot join this study group")
        
        return attrs


class CourseStatsSerializer(serializers.Serializer):
    """Serializer for course statistics in dashboard"""
    total_courses = serializers.IntegerField(
        help_text="Total number of courses in user's institution"
    )
    active_courses = serializers.IntegerField(
        help_text="Number of currently active courses"
    )
    enrolled_courses = serializers.IntegerField(
        help_text="Number of courses user is enrolled in"
    )
    teaching_courses = serializers.IntegerField(
        help_text="Number of courses user is teaching"
    )
    current_semester_courses = serializers.IntegerField(
        help_text="Number of courses in current semester"
    )
    total_students = serializers.IntegerField(
        help_text="Total number of enrolled students across all courses"
    )


class StudyGroupStatsSerializer(serializers.Serializer):
    """Serializer for study group statistics in dashboard"""
    total_groups = serializers.IntegerField(
        help_text="Total number of study groups available to user"
    )
    public_groups = serializers.IntegerField(
        help_text="Number of public study groups"
    )
    private_groups = serializers.IntegerField(
        help_text="Number of private study groups"
    )
    course_groups = serializers.IntegerField(
        help_text="Number of course-specific study groups"
    )
    general_groups = serializers.IntegerField(
        help_text="Number of general study groups"
    )
    user_groups = serializers.IntegerField(
        help_text="Number of groups user is a member of"
    )
    user_moderated_groups = serializers.IntegerField(
        help_text="Number of groups user moderates"
    )


class UpcomingMeetingSerializer(serializers.Serializer):
    """Serializer for upcoming meeting information"""
    id = serializers.IntegerField(
        help_text="Study group ID"
    )
    name = serializers.CharField(
        help_text="Study group name"
    )
    meeting_time = serializers.DateTimeField(
        help_text="Scheduled meeting time"
    )
    meeting_location = serializers.CharField(
        help_text="Meeting location"
    )
    course = serializers.CharField(
        allow_null=True,
        help_text="Associated course code (if any)"
    )


class AcademicDashboardSerializer(serializers.Serializer):
    """Serializer for academic dashboard data"""
    courses = CourseStatsSerializer(
        help_text="Course-related statistics"
    )
    study_groups = StudyGroupStatsSerializer(
        help_text="Study group-related statistics"
    )
    recent_courses = CourseListSerializer(
        many=True,
        help_text="Recently accessed courses"
    )
    recent_study_groups = StudyGroupListSerializer(
        many=True,
        help_text="Recently accessed study groups"
    )
    upcoming_meetings = UpcomingMeetingSerializer(
        many=True,
        help_text="Upcoming study group meetings"
    )


class CourseSearchSerializer(serializers.Serializer):
    """Serializer for course search parameters"""
    search = serializers.CharField(
        required=False,
        help_text="Search term for course code, name, or instructor"
    )
    semester = serializers.ChoiceField(
        choices=Course.SEMESTER_CHOICES,
        required=False,
        help_text="Filter by semester"
    )
    year = serializers.IntegerField(
        required=False,
        help_text="Filter by academic year"
    )
    instructor = serializers.IntegerField(
        required=False,
        help_text="Filter by instructor ID"
    )
    enrollment_open = serializers.BooleanField(
        required=False,
        help_text="Filter by enrollment status"
    )
    my_courses = serializers.BooleanField(
        required=False,
        help_text="Show only user's enrolled courses"
    )


class StudyGroupSearchSerializer(serializers.Serializer):
    """Serializer for study group search parameters"""
    search = serializers.CharField(
        required=False,
        help_text="Search term for group name or description"
    )
    course = serializers.IntegerField(
        required=False,
        help_text="Filter by course ID"
    )
    is_private = serializers.BooleanField(
        required=False,
        help_text="Filter by privacy level"
    )
    meeting_frequency = serializers.ChoiceField(
        choices=StudyGroup._meta.get_field('meeting_frequency').choices,
        required=False,
        help_text="Filter by meeting frequency"
    )
    my_groups = serializers.BooleanField(
        required=False,
        help_text="Show only user's groups"
    )