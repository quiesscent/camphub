from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Course, CourseEnrollment, StudyGroup, StudyGroupMember
from users.models import Institution, Campus

User = get_user_model()


class CourseForm(forms.ModelForm):
    """Form for creating and editing courses"""
    
    class Meta:
        model = Course
        fields = [
            'institution', 'course_code', 'course_name', 'semester', 
            'year', 'instructor', 'description', 'max_enrollment', 
            'enrollment_open', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 50}),
            'course_code': forms.TextInput(attrs={'placeholder': 'e.g., CS 101, MATH 201'}),
            'course_name': forms.TextInput(attrs={'placeholder': 'e.g., Introduction to Computer Science'}),
            'max_enrollment': forms.NumberInput(attrs={'min': 1, 'max': 500}),
            'year': forms.NumberInput(attrs={'min': 2020, 'max': 2030}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If user is provided, filter institution and instructor choices
        if user and hasattr(user, 'profile'):
            user_institution = user.profile.institution
            self.fields['institution'].queryset = Institution.objects.filter(id=user_institution.id)
            self.fields['instructor'].queryset = User.objects.filter(
                profile__institution=user_institution,
                profile__role__in=['faculty', 'staff']
            )
        else:
            self.fields['instructor'].queryset = User.objects.filter(
                profile__role__in=['faculty', 'staff']
            )
    
    def clean(self):
        cleaned_data = super().clean()
        institution = cleaned_data.get('institution')
        instructor = cleaned_data.get('instructor')
        year = cleaned_data.get('year')
        
        # Validate instructor belongs to the same institution
        if instructor and institution:
            if hasattr(instructor, 'profile'):
                if instructor.profile.institution != institution:
                    raise ValidationError({
                        'instructor': 'Instructor must belong to the same institution as the course.'
                    })
        
        # Validate year is not in the past for new courses
        if not self.instance.pk and year and year < timezone.now().year:
            raise ValidationError({
                'year': 'Cannot create courses for past years.'
            })
        
        return cleaned_data
    
    def clean_course_code(self):
        course_code = self.cleaned_data['course_code'].upper()
        return course_code


class CourseEnrollmentForm(forms.ModelForm):
    """Form for managing course enrollments"""
    
    class Meta:
        model = CourseEnrollment
        fields = ['user', 'course', 'role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter courses if course is provided
        if course:
            self.fields['course'].queryset = Course.objects.filter(id=course.id)
            self.fields['course'].initial = course
            self.fields['course'].widget.attrs['readonly'] = True
        
        # Filter users if user is provided
        if user:
            self.fields['user'].queryset = User.objects.filter(id=user.id)
            self.fields['user'].initial = user
            self.fields['user'].widget.attrs['readonly'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        course = cleaned_data.get('course')
        role = cleaned_data.get('role')
        
        if user and course:
            # Check if user belongs to same institution
            if hasattr(user, 'profile'):
                if user.profile.institution != course.institution:
                    raise ValidationError('User and course must belong to the same institution.')
            
            # Check enrollment limits
            if not course.can_enroll(user) and not self.instance.pk:
                if course.is_enrollment_full():
                    raise ValidationError('Course enrollment is full.')
                elif not course.enrollment_open:
                    raise ValidationError('Course enrollment is closed.')
                elif not course.is_active:
                    raise ValidationError('Course is not active.')
            
            # Validate role permissions
            if role in ['ta', 'instructor'] and hasattr(user, 'profile'):
                if user.profile.role not in ['faculty', 'staff']:
                    raise ValidationError('Only faculty and staff can be assigned as TAs or instructors.')
        
        return cleaned_data


class StudyGroupForm(forms.ModelForm):
    """Form for creating and editing study groups"""
    
    class Meta:
        model = StudyGroup
        fields = [
            'name', 'description', 'course', 'max_members', 
            'is_private', 'meeting_location', 'meeting_time', 
            'meeting_frequency'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 50}),
            'name': forms.TextInput(attrs={'placeholder': 'Enter study group name'}),
            'max_members': forms.NumberInput(attrs={'min': 2, 'max': 50}),
            'meeting_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'meeting_location': forms.TextInput(
                attrs={'placeholder': 'e.g., Library Room 101, Online via Zoom'}
            ),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter courses to only those the user is enrolled in
        if user:
            enrolled_courses = Course.objects.filter(
                enrollments__user=user,
                enrollments__is_active=True,
                is_active=True
            )
            self.fields['course'].queryset = enrolled_courses
            self.fields['course'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        meeting_time = cleaned_data.get('meeting_time')
        
        # Validate meeting time is not in the past for new groups
        if meeting_time and not self.instance.pk:
            if meeting_time < timezone.now():
                raise ValidationError({
                    'meeting_time': 'Meeting time cannot be in the past.'
                })
        
        return cleaned_data


class JoinStudyGroupForm(forms.Form):
    """Form for joining study groups"""
    
    message = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Optional message to group moderators...'
        }),
        help_text='Leave a message for the group moderators (optional for public groups, required for private groups)'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.study_group = kwargs.pop('study_group', None)
        super().__init__(*args, **kwargs)
        
        # Make message required for private groups
        if self.study_group and self.study_group.is_private:
            self.fields['message'].required = True
            self.fields['message'].help_text = 'Message is required for private groups'
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.user and self.study_group:
            if not self.study_group.can_join(self.user):
                if self.study_group.is_full():
                    raise ValidationError('Study group is full.')
                elif not self.study_group.is_active:
                    raise ValidationError('Study group is not active.')
                elif StudyGroupMember.objects.filter(
                    group=self.study_group, user=self.user, is_active=True
                ).exists():
                    raise ValidationError('You are already a member of this study group.')
                else:
                    raise ValidationError('You cannot join this study group.')
        
        return cleaned_data


class StudyGroupSearchForm(forms.Form):
    """Form for searching study groups"""
    
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search study groups...',
            'class': 'form-control'
        })
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        required=False,
        empty_label="All Courses",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_private = forms.ChoiceField(
        choices=[('', 'All'), ('False', 'Public'), ('True', 'Private')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    meeting_frequency = forms.ChoiceField(
        choices=[('', 'Any Frequency')] + StudyGroup._meta.get_field('meeting_frequency').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter courses to user's institution
        if user and hasattr(user, 'profile'):
            self.fields['course'].queryset = Course.objects.filter(
                institution=user.profile.institution,
                is_active=True
            ).order_by('course_code')


class CourseSearchForm(forms.Form):
    """Form for searching courses"""
    
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search courses...',
            'class': 'form-control'
        })
    )
    semester = forms.ChoiceField(
        choices=[('', 'All Semesters')] + Course.SEMESTER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Year'
        })
    )
    instructor = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="All Instructors",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    enrollment_open = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Enrollment Open'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter instructors to user's institution
        if user and hasattr(user, 'profile'):
            self.fields['instructor'].queryset = User.objects.filter(
                profile__institution=user.profile.institution,
                profile__role__in=['faculty', 'staff']
            ).order_by('first_name', 'last_name')


class StudyGroupMemberForm(forms.ModelForm):
    """Form for managing study group members"""
    
    class Meta:
        model = StudyGroupMember
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Only allow role changes if current user is a moderator
        if current_user and self.instance.group:
            if not self.instance.group.is_moderator(current_user):
                self.fields['role'].widget.attrs['disabled'] = True


class BulkEnrollmentForm(forms.Form):
    """Form for bulk enrolling students in courses"""
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        help_text='Select users to enroll in the course'
    )
    role = forms.ChoiceField(
        choices=CourseEnrollment.ROLE_CHOICES,
        initial='student',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        institution = kwargs.pop('institution', None)
        super().__init__(*args, **kwargs)
        
        if institution:
            # Filter courses and users by institution
            self.fields['course'].queryset = Course.objects.filter(
                institution=institution,
                is_active=True,
                enrollment_open=True
            )
            self.fields['users'].queryset = User.objects.filter(
                profile__institution=institution,
                is_active=True
            ).order_by('first_name', 'last_name')
    
    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        users = cleaned_data.get('users')
        role = cleaned_data.get('role')
        
        if course and users:
            # Check if course can accommodate all users
            current_enrollment = course.get_enrollment_count()
            if current_enrollment + len(users) > course.max_enrollment:
                raise ValidationError(
                    f'Cannot enroll {len(users)} users. Course capacity: {course.max_enrollment}, '
                    f'Current enrollment: {current_enrollment}'
                )
            
            # Check for existing enrollments
            existing_enrollments = CourseEnrollment.objects.filter(
                course=course,
                user__in=users,
                is_active=True
            )
            if existing_enrollments.exists():
                existing_users = [str(e.user) for e in existing_enrollments]
                raise ValidationError(
                    f'The following users are already enrolled: {", ".join(existing_users)}'
                )
            
            # Validate role permissions for bulk enrollment
            if role in ['ta', 'instructor']:
                invalid_users = users.filter(profile__role__in=['student'])
                if invalid_users.exists():
                    raise ValidationError(
                        f'Cannot assign {role} role to students: {", ".join([str(u) for u in invalid_users])}'
                    )
        
        return cleaned_data