from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from .models import User, UserProfile, Institution, Campus


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['id', 'name', 'domain', 'logo']
        
    name = serializers.CharField(
        help_text="Full name of the educational institution",
        read_only=True
    )
    domain = serializers.CharField(
        help_text="Email domain for institutional verification (e.g., 'university.edu')",
        read_only=True
    )
    logo = serializers.ImageField(
        help_text="Institution logo image",
        read_only=True,
        allow_null=True
    )


class CampusSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    
    class Meta:
        model = Campus
        fields = ['id', 'name', 'address', 'coordinates', 'institution']
        
    name = serializers.CharField(
        help_text="Campus name within the institution",
        read_only=True
    )
    address = serializers.CharField(
        help_text="Physical address of the campus",
        read_only=True
    )
    coordinates = serializers.JSONField(
        help_text="GPS coordinates as {'lat': float, 'lng': float}",
        read_only=True,
        allow_null=True
    )


class UserProfileSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    institution_id = serializers.IntegerField(
        write_only=True,
        help_text="ID of the institution this user belongs to",
        error_messages={
            'required': 'Institution is required',
            'invalid': 'Invalid institution ID'
        }
    )
    campus_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID of the campus within the institution (optional)",
        error_messages={
            'invalid': 'Invalid campus ID'
        }
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'institution', 'campus', 'institution_id', 'campus_id',
            'student_id', 'role', 'department', 'phone_number',
            'dorm_building', 'room_number', 'privacy_level'
        ]
        
    student_id = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text="Official student/employee ID number",
        error_messages={
            'max_length': 'Student ID cannot exceed 50 characters'
        }
    )
    role = serializers.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        help_text="User role: student, faculty, or staff",
        error_messages={
            'invalid_choice': 'Role must be one of: student, faculty, staff'
        }
    )
    department = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Academic department or administrative unit",
        error_messages={
            'max_length': 'Department name cannot exceed 100 characters'
        }
    )
    phone_number = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        validators=[RegexValidator(
            regex=r'^\+?[\d\s\-\(\)]+$',
            message='Enter a valid phone number'
        )],
        help_text="Contact phone number with country code",
        error_messages={
            'max_length': 'Phone number cannot exceed 20 characters'
        }
    )
    dorm_building = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Name of dormitory building (for residential students)",
        error_messages={
            'max_length': 'Building name cannot exceed 100 characters'
        }
    )
    room_number = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Dorm room number",
        error_messages={
            'max_length': 'Room number cannot exceed 20 characters'
        }
    )
    privacy_level = serializers.ChoiceField(
        choices=UserProfile.PRIVACY_CHOICES,
        help_text="Profile visibility: public, friends, or private",
        error_messages={
            'invalid_choice': 'Privacy level must be one of: public, friends, private'
        }
    )


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'profile_picture', 'bio', 'graduation_year', 'major',
            'is_verified', 'profile', 'created_at'
        ]
        read_only_fields = ['id', 'username', 'is_verified', 'created_at']
        
    email = serializers.EmailField(
        help_text="Institutional email address for verification",
        error_messages={
            'required': 'Email address is required',
            'invalid': 'Enter a valid email address'
        }
    )
    first_name = serializers.CharField(
        max_length=30,
        help_text="User's first name",
        error_messages={
            'required': 'First name is required',
            'max_length': 'First name cannot exceed 30 characters'
        }
    )
    last_name = serializers.CharField(
        max_length=30,
        help_text="User's last name",
        error_messages={
            'required': 'Last name is required',
            'max_length': 'Last name cannot exceed 30 characters'
        }
    )
    profile_picture = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Profile picture (JPEG, PNG, max 5MB, auto-optimized)",
        error_messages={
            'invalid_image': 'Upload a valid image file'
        }
    )
    bio = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Short biography or personal description",
        error_messages={
            'max_length': 'Bio cannot exceed 500 characters'
        }
    )
    graduation_year = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Expected or actual graduation year",
        error_messages={
            'invalid': 'Enter a valid year'
        }
    )
    major = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Field of study or academic major",
        error_messages={
            'max_length': 'Major cannot exceed 100 characters'
        }
    )


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Institutional email address (must match institution domain)",
        error_messages={
            'required': 'Email address is required',
            'invalid': 'Enter a valid email address'
        }
    )
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="Password (minimum 8 characters, cannot be too common)",
        error_messages={
            'required': 'Password is required'
        }
    )
    first_name = serializers.CharField(
        max_length=30,
        help_text="First name",
        error_messages={
            'required': 'First name is required',
            'max_length': 'First name cannot exceed 30 characters'
        }
    )
    last_name = serializers.CharField(
        max_length=30,
        help_text="Last name",
        error_messages={
            'required': 'Last name is required',
            'max_length': 'Last name cannot exceed 30 characters'
        }
    )
    student_id = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text="Student/employee ID number (optional)",
        error_messages={
            'max_length': 'Student ID cannot exceed 50 characters'
        }
    )
    major = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Academic major or field of study (optional)",
        error_messages={
            'max_length': 'Major cannot exceed 100 characters'
        }
    )
    graduation_year = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Expected graduation year (optional)",
        error_messages={
            'invalid': 'Enter a valid year'
        }
    )
    institution_id = serializers.IntegerField(
        help_text="ID of the institution you belong to",
        error_messages={
            'required': 'Institution is required',
            'invalid': 'Invalid institution ID'
        }
    )
    
    def validate(self, attrs):
        email_domain = attrs['email'].split('@')[1]
        institution_id = attrs['institution_id']
        
        try:
            institution = Institution.objects.get(id=institution_id)
            if institution.domain != email_domain:
                raise serializers.ValidationError({
                    'email': [f"Email must be from {institution.domain} domain"]
                })
        except Institution.DoesNotExist:
            raise serializers.ValidationError({
                'institution_id': ['Invalid institution']
            })
        
        return attrs
    
    def create(self, validated_data):
        institution_id = validated_data.pop('institution_id')
        student_id = validated_data.pop('student_id', '')
        
        username = validated_data['email'].split('@')[0]
        validated_data['username'] = username
        
        user = User.objects.create_user(**validated_data)
        
        UserProfile.objects.create(
            user=user,
            institution_id=institution_id,
            student_id=student_id
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Your institutional email address",
        error_messages={
            'required': 'Email address is required',
            'invalid': 'Enter a valid email address'
        }
    )
    password = serializers.CharField(
        write_only=True,
        help_text="Your account password",
        error_messages={
            'required': 'Password is required'
        }
    )
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError({
                    'non_field_errors': ['Unable to log in with provided credentials.']
                })
            
            if not user.is_active:
                raise serializers.ValidationError({
                    'non_field_errors': ['User account is disabled.']
                })
                
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError({
                'non_field_errors': ['Must include email and password.']
            })


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
        help_text="Your current password",
        error_messages={
            'required': 'Current password is required'
        }
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="New password (minimum 8 characters, cannot be too common)",
        error_messages={
            'required': 'New password is required'
        }
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        help_text="Confirm your new password",
        error_messages={
            'required': 'Password confirmation is required'
        }
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': ["New passwords don't match"]
            })
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


class EmailVerificationSerializer(serializers.Serializer):
    uid = serializers.CharField(
        help_text="User ID encoded in base64 from verification email",
        error_messages={
            'required': 'User ID is required',
            'blank': 'User ID cannot be blank'
        }
    )
    token = serializers.CharField(
        help_text="Verification token from email",
        error_messages={
            'required': 'Verification token is required',
            'blank': 'Token cannot be blank'
        }
    )


class UserProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        max_length=30,
        required=False,
        help_text="First name",
        error_messages={
            'max_length': 'First name cannot exceed 30 characters'
        }
    )
    last_name = serializers.CharField(
        max_length=30,
        required=False,
        help_text="Last name",
        error_messages={
            'max_length': 'Last name cannot exceed 30 characters'
        }
    )
    bio = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Short biography or personal description",
        error_messages={
            'max_length': 'Bio cannot exceed 500 characters'
        }
    )
    major = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Academic major or field of study",
        error_messages={
            'max_length': 'Major cannot exceed 100 characters'
        }
    )
    graduation_year = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Expected or actual graduation year",
        error_messages={
            'invalid': 'Enter a valid year'
        }
    )
    privacy_settings = serializers.JSONField(
        required=False,
        help_text="Privacy preferences as JSON object",
        error_messages={
            'invalid': 'Invalid JSON format for privacy settings'
        }
    )
    dorm_building = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Dormitory building name",
        error_messages={
            'max_length': 'Building name cannot exceed 100 characters'
        }
    )
    room_number = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Room number",
        error_messages={
            'max_length': 'Room number cannot exceed 20 characters'
        }
    )
