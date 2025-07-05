from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
import datetime

User = get_user_model()

class CourseManager(models.Manager):
    """Custom manager for Course model"""
    
    def active(self):
        """Return only active courses"""
        return self.filter(is_active=True)
    
    def current_semester(self):
        """Return courses for current semester"""
        current_year = timezone.now().year
        return self.filter(year=current_year, is_active=True)
    
    def by_institution(self, institution):
        """Return courses for specific institution"""
        return self.filter(institution=institution, is_active=True)
    
    def search(self, query):
        """Search courses by name or code"""
        return self.filter(
            models.Q(course_name__icontains=query) |
            models.Q(course_code__icontains=query)
        )

class Course(models.Model):
    """
    Model representing academic courses offered by institutions.
    Handles course information, scheduling, and instructor assignment.
    """
    
    SEMESTER_CHOICES = [
        ('fall', 'Fall'),
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('winter', 'Winter'),
    ]
    
    # Course identification
    institution = models.ForeignKey(
        'users.Institution',  # Assuming Institution model is in users app
        on_delete=models.CASCADE,
        related_name='courses',
        help_text="Institution offering this course"
    )
    course_code = models.CharField(
        max_length=20,
        help_text="Course code (e.g., CS 101, MATH 201)"
    )
    course_name = models.CharField(
        max_length=200,
        help_text="Full course name"
    )
    
    # Academic period
    semester = models.CharField(
        max_length=10,
        choices=SEMESTER_CHOICES,
        help_text="Academic semester"
    )
    year = models.IntegerField(
        validators=[
            MinValueValidator(2020),
            MaxValueValidator(2030)
        ],
        help_text="Academic year"
    )
    
    # Course details
    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='taught_courses',
        limit_choices_to={'profile__role': 'faculty'},  # Fixed: use 'profile' instead of 'userprofile'
        help_text="Primary instructor for this course"
    )
    description = models.TextField(
        blank=True,
        help_text="Course description and objectives"
    )
    
    # Course settings
    max_enrollment = models.IntegerField(
        default=100,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of students"
    )
    enrollment_open = models.BooleanField(
        default=True,
        help_text="Whether enrollment is currently open"
    )
    
    # Status and metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the course is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Custom manager
    objects = CourseManager()
    
    class Meta:
        db_table = 'academic_courses'
        unique_together = ['institution', 'course_code', 'semester', 'year']
        ordering = ['-year', 'semester', 'course_code']
        indexes = [
            models.Index(fields=['institution', 'is_active']),
            models.Index(fields=['year', 'semester']),
            models.Index(fields=['course_code']),
        ]
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
    
    def __str__(self):
        return f"{self.course_code} - {self.course_name} ({self.semester} {self.year})"
    
    def clean(self):
        """Validate course data"""
        # Ensure instructor belongs to the same institution
        if self.instructor and hasattr(self.instructor, 'profile'):  # Fixed: use 'profile'
            if self.instructor.profile.institution != self.institution:
                raise ValidationError("Instructor must belong to the same institution as the course")
        
        # Validate year is not in the past (for new courses)
        if not self.pk and self.year < timezone.now().year:
            raise ValidationError("Cannot create courses for past years")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('academic:course_detail', kwargs={'pk': self.pk})
    
    def get_enrolled_students(self):
        """Get all students enrolled in this course"""
        return User.objects.filter(
            course_enrollments__course=self,
            course_enrollments__role='student',
            course_enrollments__is_active=True
        )
    
    def get_study_groups(self):
        """Get all study groups for this course"""
        return self.study_groups.filter(is_active=True)
    
    def get_enrollment_count(self):
        """Get current enrollment count"""
        return self.enrollments.filter(is_active=True).count()
    
    def is_enrollment_full(self):
        """Check if course enrollment is full"""
        return self.get_enrollment_count() >= self.max_enrollment
    
    def can_enroll(self, user):
        """Check if user can enroll in this course"""
        if not self.enrollment_open or not self.is_active:
            return False
        if self.is_enrollment_full():
            return False
        if hasattr(user, 'profile') and user.profile.institution != self.institution:  # Fixed: use 'profile'
            return False
        return not self.enrollments.filter(user=user, is_active=True).exists()
    
    @property
    def semester_display(self):
        """Get formatted semester display"""
        return f"{self.get_semester_display()} {self.year}"


class CourseEnrollment(models.Model):
    """
    Model representing user enrollment in courses.
    Tracks student, TA, and instructor relationships with courses.
    """
    
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('ta', 'Teaching Assistant'),
        ('instructor', 'Instructor'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='course_enrollments',
        help_text="User enrolled in the course"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        help_text="Course being enrolled in"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        help_text="User's role in the course"
    )
    enrollment_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Date when enrollment was created"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether enrollment is currently active"
    )
    
    # Optional fields for additional tracking
    grade = models.CharField(
        max_length=5,
        blank=True,
        help_text="Final grade (optional)"
    )
    completion_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when course was completed"
    )
    
    class Meta:
        db_table = 'academic_course_enrollments'
        unique_together = ['user', 'course']
        ordering = ['-enrollment_date']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['course', 'role']),
            models.Index(fields=['enrollment_date']),
        ]
        verbose_name = 'Course Enrollment'
        verbose_name_plural = 'Course Enrollments'
    
    def __str__(self):
        return f"{self.user} - {self.course} ({self.get_role_display()})"
    
    def clean(self):
        """Validate enrollment data"""
        # Ensure user and course belong to same institution
        if (self.user and self.course and 
            hasattr(self.user, 'profile') and  # Fixed: use 'profile'
            self.user.profile.institution != self.course.institution):
            raise ValidationError("User and course must belong to the same institution")
        
        # Validate role permissions
        if self.role in ['ta', 'instructor'] and hasattr(self.user, 'profile'):  # Fixed: use 'profile'
            if self.user.profile.role not in ['faculty', 'staff']:
                raise ValidationError("Only faculty and staff can be assigned as TAs or instructors")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_role_display_with_icon(self):
        """Get role display with appropriate icon"""
        icons = {
            'student': '👨‍🎓',
            'ta': '👨‍🏫',
            'instructor': '👨‍🏫'
        }
        return f"{icons.get(self.role, '')} {self.get_role_display()}"


class StudyGroupManager(models.Manager):
    """Custom manager for StudyGroup model"""
    
    def active(self):
        """Return only active study groups"""
        return self.filter(is_active=True)
    
    def public(self):
        """Return only public study groups"""
        return self.filter(is_private=False, is_active=True)
    
    def for_course(self, course):
        """Return study groups for specific course"""
        return self.filter(course=course, is_active=True)
    
    def user_can_join(self, user):
        """Return study groups that user can join"""
        return self.filter(
            is_active=True,
            members__lt=models.F('max_members')
        ).exclude(
            study_group_members__user=user,
            study_group_members__is_active=True
        )


class StudyGroup(models.Model):
    """
    Model representing study groups for courses or general academic purposes.
    Handles group creation, membership management, and meeting coordination.
    """
    
    name = models.CharField(
        max_length=200,
        help_text="Name of the study group"
    )
    description = models.TextField(
        help_text="Description of the study group's purpose and goals"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='study_groups',
        null=True,
        blank=True,
        help_text="Associated course (optional for general study groups)"
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_study_groups',
        help_text="User who created the study group"
    )
    
    # Group settings
    max_members = models.IntegerField(
        default=10,
        validators=[MinValueValidator(2), MaxValueValidator(50)],
        help_text="Maximum number of members allowed"
    )
    is_private = models.BooleanField(
        default=False,
        help_text="Whether group requires approval to join"
    )
    
    # Meeting information
    meeting_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Regular meeting location"
    )
    meeting_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Regular meeting time"
    )
    meeting_frequency = models.CharField(
        max_length=20,
        choices=[
            ('weekly', 'Weekly'),
            ('biweekly', 'Bi-weekly'),
            ('monthly', 'Monthly'),
            ('irregular', 'Irregular'),
        ],
        default='weekly',
        help_text="How often the group meets"
    )
    
    # Status and metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the study group is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Custom manager
    objects = StudyGroupManager()
    
    class Meta:
        db_table = 'academic_study_groups'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'is_active']),
            models.Index(fields=['creator', 'is_active']),
            models.Index(fields=['is_private', 'is_active']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Study Group'
        verbose_name_plural = 'Study Groups'
    
    def __str__(self):
        course_info = f" ({self.course.course_code})" if self.course else ""
        return f"{self.name}{course_info}"
    
    def clean(self):
        """Validate study group data"""
        # If course is specified, ensure creator is enrolled
        if self.course and self.creator_id:  # Fixed: use creator_id instead of creator
            if not self.course.enrollments.filter(user_id=self.creator_id, is_active=True).exists():
                raise ValidationError("Creator must be enrolled in the course")
        
        # Validate meeting time is not in the past (for new groups)
        if self.meeting_time and not self.pk and self.meeting_time < timezone.now():
            raise ValidationError("Meeting time cannot be in the past")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # Automatically add creator as a moderator
        if is_new:
            StudyGroupMember.objects.create(
                group=self,
                user=self.creator,
                role='moderator'
            )
    
    def get_absolute_url(self):
        return reverse('academic:study_group_detail', kwargs={'pk': self.pk})
    
    def get_members(self):
        """Get all active members"""
        return User.objects.filter(
            study_group_memberships__group=self,
            study_group_memberships__is_active=True
        )
    
    def get_member_count(self):
        """Get current member count"""
        return self.members.filter(is_active=True).count()
    
    def is_full(self):
        """Check if study group is at capacity"""
        return self.get_member_count() >= self.max_members
    
    def can_join(self, user):
        """Check if user can join this study group"""
        if not self.is_active or self.is_full():
            return False
        
        # Check if user is already a member
        if self.members.filter(user=user, is_active=True).exists():
            return False
        
        # If course-specific, check if user is enrolled
        if self.course:
            if not self.course.enrollments.filter(user=user, is_active=True).exists():
                return False
        
        return True
    
    def get_moderators(self):
        """Get all moderators"""
        return User.objects.filter(
            study_group_memberships__group=self,
            study_group_memberships__role='moderator',
            study_group_memberships__is_active=True
        )
    
    def is_moderator(self, user):
        """Check if user is a moderator"""
        return self.members.filter(
            user=user,
            role='moderator',
            is_active=True
        ).exists()
    
    @property
    def next_meeting(self):
        """Get next meeting time based on frequency"""
        if not self.meeting_time:
            return None
        
        # Simple calculation - in real app, you'd want more sophisticated scheduling
        now = timezone.now()
        if self.meeting_time > now:
            return self.meeting_time
        
        # Calculate next meeting based on frequency
        if self.meeting_frequency == 'weekly':
            days_ahead = 7
        elif self.meeting_frequency == 'biweekly':
            days_ahead = 14
        elif self.meeting_frequency == 'monthly':
            days_ahead = 30
        else:
            return None
        
        return self.meeting_time + datetime.timedelta(days=days_ahead)


class StudyGroupMember(models.Model):
    """
    Model representing membership in study groups.
    Tracks member roles and participation.
    """
    
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
    ]
    
    group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name='members',
        help_text="Study group this membership belongs to"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='study_group_memberships',
        help_text="User who is a member"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        help_text="Member's role in the group"
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date when user joined the group"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether membership is currently active"
    )
    
    # Optional tracking fields
    last_active = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time member was active in group"
    )
    contributions = models.IntegerField(
        default=0,
        help_text="Number of contributions/posts in group"
    )
    
    class Meta:
        db_table = 'academic_study_group_members'
        unique_together = ['group', 'user']
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['group', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['role']),
        ]
        verbose_name = 'Study Group Member'
        verbose_name_plural = 'Study Group Members'
    
    def __str__(self):
        return f"{self.user} in {self.group.name} ({self.get_role_display()})"
    
    def clean(self):
        """Validate membership data"""
        # Ensure user can join the group
        if not self.pk and not self.group.can_join(self.user):
            raise ValidationError("User cannot join this study group")
        
        # If course-specific group, ensure user is enrolled
        if self.group.course:
            if not self.group.course.enrollments.filter(user=self.user, is_active=True).exists():
                raise ValidationError("User must be enrolled in the course to join this study group")
    
    def save(self, *args, **kwargs):
        if not self.pk:  # New membership
            self.full_clean()
        super().save(*args, **kwargs)
    
    def promote_to_moderator(self):
        """Promote member to moderator"""
        self.role = 'moderator'
        self.save()
    
    def demote_to_member(self):
        """Demote moderator to regular member"""
        self.role = 'member'
        self.save()
    
    def leave_group(self):
        """Leave the study group"""
        self.is_active = False
        self.save()
    
    def get_role_display_with_icon(self):
        """Get role display with appropriate icon"""
        icons = {
            'member': '👥',
            'moderator': '⭐'
        }
        return f"{icons.get(self.role, '')} {self.get_role_display()}"