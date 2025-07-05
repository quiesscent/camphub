from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, Institution, Campus


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['id', 'name', 'domain', 'logo']


class CampusSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    
    class Meta:
        model = Campus
        fields = ['id', 'name', 'address', 'coordinates', 'institution']


class UserProfileSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    institution_id = serializers.IntegerField(write_only=True)
    campus_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'institution', 'campus', 'institution_id', 'campus_id',
            'student_id', 'role', 'department', 'phone_number',
            'dorm_building', 'room_number', 'privacy_level'
        ]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'profile_picture', 'bio', 'graduation_year', 'major',
            'is_verified', 'profile', 'created_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at']


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    student_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    major = serializers.CharField(max_length=100, required=False, allow_blank=True)
    graduation_year = serializers.IntegerField(required=False, allow_null=True)
    institution_id = serializers.IntegerField()
    
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
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
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
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value
