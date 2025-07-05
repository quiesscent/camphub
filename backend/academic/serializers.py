from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Count
from .models import Course, CourseEnrollment, StudyGroup, StudyGroupMember
from users.serializers import UserSerializer, InstitutionSerializer

User = get_user_model()


class CourseInstructorSerializer(serializers.ModelSerializer):
    """Simplified instructor serializer for course listings"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'full_name', 'email', 'profile_picture']


class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for course list view"""
    instructor = CourseInstructorSerializer(read_only=True)
    institution = InstitutionSerializer(read_only=True)
    enrollment_count = serializers.IntegerField(read_only=True)
    study_groups_count = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    semester_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'course_code', 'course_name', 'semester', 'year',
            'semester_display', 'instructor', 'institution', 'description',
            'max_enrollment', 'enrollment_count', 'study_groups_count',
            'enrollment_open', 'is_active', 'is_enrolled', 'user_role',
            'created_at', 'updated_at'
        ]
    
    def get_is_enrolled(self, obj):
        """Check if current user is enrolled in the course"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(user=request.user, is_active=True).exists()
        return False
    
    def get_user_role(self, obj):
        """Get current user's role in the course"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            enrollment = obj.enrollments.filter(user=request.user, is_active=True).first()
            return enrollment.role if enrollment else None
        return None


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for course detail view"""
    instructor = CourseInstructorSerializer(read_only=True)
    institution = InstitutionSerializer(read_only=True)
    enrollment_count = serializers.IntegerField(read_only=True)
    study_groups_count = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    can_enroll = serializers.SerializerMethodField()
    semester_display = serializers.CharField(read_only=True)
    enrolled_students = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'course_code', 'course_name', 'semester', 'year',
            'semester_display', 'instructor', 'institution', 'description',
            'max_enrollment', 'enrollment_count', 'study_groups_count',
            'enrollment_open', 'is_active', 'is_enrolled', 'user_role',
            'can_enroll', 'enrolled_students', 'created_at', 'updated_at'
        ]
    
    def get_is_enrolled(self, obj):
        """Check if current user is enrolled in the course"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(user=request.user, is_active=True).exists()
        return False
    
    def get_user_role(self, obj):
        """Get current user's role in the course"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            enrollment = obj.enrollments.filter(user=request.user, is_active=True).first()
            return enrollment.role if enrollment else None
        return None
    
    def get_can_enroll(self, obj):
        """Check if current user can enroll in the course"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_enroll(request.user)
        return False
    
    def get_enrolled_students(self, obj):
        """Get list of enrolled students (only for instructors/TAs)"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user_enrollment = obj.enrollments.filter(user=request.user, is_active=True).first()
            if user_enrollment and user_enrollment.role in ['instructor', 'ta']:
                students = obj.get_enrolled_students()[:10]  # Limit to 10 for performance
                return CourseInstructorSerializer(students, many=True).data
        return []


class CourseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating courses"""
    instructor_id = serializers.IntegerField(write_only=True)
    institution_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Course
        fields = [
            'course_code', 'course_name', 'semester', 'year',
            'instructor_id', 'institution_id', 'description',
            'max_enrollment', 'enrollment_open'
        ]
    
    def validate(self, attrs):
        instructor_id = attrs.get('instructor_id')
        institution_id = attrs.get('institution_id')
        
        # Validate instructor exists and belongs to institution
        try:
            instructor = User.objects.get(id=instructor_id)
            if hasattr(instructor, 'profile'):
                if instructor.profile.institution_id != institution_id:
                    raise serializers.ValidationError(
                        "Instructor must belong to the same institution as the course"
                    )
            else:
                raise serializers.ValidationError("Instructor must have a valid profile")
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid instructor")
        
        return attrs
    
    def create(self, validated_data):
        instructor_id = validated_data.pop('instructor_id')
        institution_id = validated_data.pop('institution_id')
        
        course = Course.objects.create(
            instructor_id=instructor_id,
            institution_id=institution_id,
            **validated_data
        )
        return course


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for course enrollments"""
    user = UserSerializer(read_only=True)
    course = CourseListSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'user', 'course', 'role', 'role_display',
            'enrollment_date', 'is_active', 'grade', 'completion_date'
        ]


class EnrollInCourseSerializer(serializers.Serializer):
    """Serializer for enrolling in a course"""
    course_id = serializers.IntegerField()
    
    def validate_course_id(self, value):
        try:
            course = Course.objects.get(id=value, is_active=True)
            return value
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found or not active")
    
    def validate(self, attrs):
        course_id = attrs.get('course_id')
        request = self.context.get('request')
        
        if request and request.user.is_authenticated:
            course = Course.objects.get(id=course_id)
            if not course.can_enroll(request.user):
                if course.is_enrollment_full():
                    raise serializers.ValidationError("Course enrollment is full")
                elif not course.enrollment_open:
                    raise serializers.ValidationError("Course enrollment is closed")
                else:
                    raise serializers.ValidationError("Cannot enroll in this course")
        
        return attrs


class StudyGroupMemberSerializer(serializers.ModelSerializer):
    """Serializer for study group members"""
    user = UserSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display_with_icon', read_only=True)
    
    class Meta:
        model = StudyGroupMember
        fields = [
            'id', 'user', 'role', 'role_display', 'joined_at',
            'is_active', 'contributions', 'last_active'
        ]


class StudyGroupListSerializer(serializers.ModelSerializer):
    """Serializer for study group list view"""
    creator = UserSerializer(read_only=True)
    course = CourseListSerializer(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    is_member = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    next_meeting = serializers.CharField(read_only=True)
    
    class Meta:
        model = StudyGroup
        fields = [
            'id', 'name', 'description', 'course', 'creator',
            'max_members', 'member_count', 'is_private', 'is_member',
            'can_join', 'user_role', 'meeting_location', 'meeting_time',
            'meeting_frequency', 'next_meeting', 'is_active', 'created_at'
        ]
    
    def get_is_member(self, obj):
        """Check if current user is a member of the study group"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.members.filter(user=request.user, is_active=True).exists()
        return False
    
    def get_can_join(self, obj):
        """Check if current user can join the study group"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_join(request.user)
        return False
    
    def get_user_role(self, obj):
        """Get current user's role in the study group"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = obj.members.filter(user=request.user, is_active=True).first()
            return membership.role if membership else None
        return None


class StudyGroupDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for study group detail view"""
    creator = UserSerializer(read_only=True)
    course = CourseDetailSerializer(read_only=True)
    members = StudyGroupMemberSerializer(many=True, read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    is_member = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    is_moderator = serializers.SerializerMethodField()
    next_meeting = serializers.CharField(read_only=True)
    
    class Meta:
        model = StudyGroup
        fields = [
            'id', 'name', 'description', 'course', 'creator', 'members',
            'max_members', 'member_count', 'is_private', 'is_member',
            'can_join', 'user_role', 'is_moderator', 'meeting_location',
            'meeting_time', 'meeting_frequency', 'next_meeting',
            'is_active', 'created_at', 'updated_at'
        ]
    
    def get_is_member(self, obj):
        """Check if current user is a member of the study group"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.members.filter(user=request.user, is_active=True).exists()
        return False
    
    def get_can_join(self, obj):
        """Check if current user can join the study group"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_join(request.user)
        return False
    
    def get_user_role(self, obj):
        """Get current user's role in the study group"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = obj.members.filter(user=request.user, is_active=True).first()
            return membership.role if membership else None
        return None
    
    def get_is_moderator(self, obj):
        """Check if current user is a moderator of the study group"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_moderator(request.user)
        return False


class StudyGroupCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating study groups"""
    course_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = StudyGroup
        fields = [
            'name', 'description', 'course_id', 'max_members',
            'is_private', 'meeting_location', 'meeting_time', 'meeting_frequency'
        ]
    
    def validate_course_id(self, value):
        if value is not None:
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                # Check if user is enrolled in the course
                if not CourseEnrollment.objects.filter(
                    course_id=value, user=request.user, is_active=True
                ).exists():
                    raise serializers.ValidationError(
                        "You must be enrolled in the course to create a study group for it"
                    )
        return value
    
    def create(self, validated_data):
        course_id = validated_data.pop('course_id', None)
        request = self.context.get('request')
        
        study_group = StudyGroup.objects.create(
            creator=request.user,
            course_id=course_id,
            **validated_data
        )
        return study_group


class JoinStudyGroupSerializer(serializers.Serializer):
    """Serializer for joining study groups"""
    message = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate(self, attrs):
        request = self.context.get('request')
        study_group = self.context.get('study_group')
        
        if request and request.user.is_authenticated and study_group:
            if not study_group.can_join(request.user):
                if study_group.is_full():
                    raise serializers.ValidationError("Study group is full")
                elif not study_group.is_active:
                    raise serializers.ValidationError("Study group is not active")
                else:
                    raise serializers.ValidationError("Cannot join this study group")
            
            # Require message for private groups
            if study_group.is_private and not attrs.get('message'):
                raise serializers.ValidationError(
                    "Message is required for private study groups"
                )
        
        return attrs


class StudyGroupStatsSerializer(serializers.Serializer):
    """Serializer for study group statistics"""
    total_groups = serializers.IntegerField()
    public_groups = serializers.IntegerField()
    private_groups = serializers.IntegerField()
    course_groups = serializers.IntegerField()
    general_groups = serializers.IntegerField()
    user_groups = serializers.IntegerField()
    user_moderated_groups = serializers.IntegerField()


class CourseStatsSerializer(serializers.Serializer):
    """Serializer for course statistics"""
    total_courses = serializers.IntegerField()
    active_courses = serializers.IntegerField()
    enrolled_courses = serializers.IntegerField()
    teaching_courses = serializers.IntegerField()
    current_semester_courses = serializers.IntegerField()
    total_students = serializers.IntegerField()


class AcademicDashboardSerializer(serializers.Serializer):
    """Serializer for academic dashboard data"""
    courses = CourseStatsSerializer()
    study_groups = StudyGroupStatsSerializer()
    recent_courses = CourseListSerializer(many=True)
    recent_study_groups = StudyGroupListSerializer(many=True)
    upcoming_meetings = serializers.ListField(child=serializers.DictField())


class BulkEnrollmentSerializer(serializers.Serializer):
    """Serializer for bulk enrollment operations"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    role = serializers.ChoiceField(choices=CourseEnrollment.ROLE_CHOICES, default='student')
    
    def validate_user_ids(self, value):
        # Check if all users exist and belong to the same institution
        users = User.objects.filter(id__in=value)
        if len(users) != len(value):
            raise serializers.ValidationError("Some users do not exist")
        
        request = self.context.get('request')
        course = self.context.get('course')
        
        if request and course:
            # Check institution matching
            invalid_users = users.exclude(profile__institution=course.institution)
            if invalid_users.exists():
                raise serializers.ValidationError(
                    "All users must belong to the same institution as the course"
                )
            
            # Check existing enrollments
            existing = CourseEnrollment.objects.filter(
                course=course, user__in=users, is_active=True
            ).values_list('user__id', flat=True)
            if existing:
                raise serializers.ValidationError(
                    f"Users with IDs {list(existing)} are already enrolled"
                )
        
        return value
    
    def validate(self, attrs):
        course = self.context.get('course')
        user_ids = attrs.get('user_ids')
        role = attrs.get('role')
        
        if course and user_ids:
            # Check enrollment capacity
            current_count = course.get_enrollment_count()
            if current_count + len(user_ids) > course.max_enrollment:
                raise serializers.ValidationError(
                    f"Cannot enroll {len(user_ids)} users. "
                    f"Course capacity: {course.max_enrollment}, Current: {current_count}"
                )
            
            # Validate role permissions
            if role in ['ta', 'instructor']:
                users = User.objects.filter(id__in=user_ids)
                invalid_users = users.filter(profile__role='student')
                if invalid_users.exists():
                    raise serializers.ValidationError(
                        f"Cannot assign {role} role to students"
                    )
        
        return attrs