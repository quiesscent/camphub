from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Event, EventAttendee, Club, ClubMember

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for nested representations
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email']
        read_only_fields = ['id', 'username', 'full_name', 'email']


class EventAttendeeSerializer(serializers.ModelSerializer):
    """
    Serializer for event attendee information
    """
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = EventAttendee
        fields = [
            'id', 'user', 'user_id', 'status', 'registered_at',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'registered_at', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Set user from context if not provided
        if 'user_id' not in validated_data:
            validated_data['user'] = self.context['request'].user
        else:
            validated_data['user_id'] = validated_data.pop('user_id')
        return super().create(validated_data)


class EventListSerializer(serializers.ModelSerializer):
    """
    Serializer for event list view with basic information
    """
    organizer = UserBasicSerializer(read_only=True)
    attendees_count = serializers.IntegerField(read_only=True)
    interested_count = serializers.IntegerField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    is_ongoing = serializers.BooleanField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    duration = serializers.FloatField(read_only=True)
    user_attendance = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'organizer', 'start_datetime',
            'end_datetime', 'location', 'event_type', 'is_public',
            'max_attendees', 'registration_required', 'cover_image',
            'institution', 'campus', 'tags', 'attendees_count',
            'interested_count', 'is_upcoming', 'is_ongoing', 'is_past',
            'is_full', 'duration', 'user_attendance', 'created_at',
            'updated_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'attendees_count', 'interested_count', 'is_upcoming',
            'is_ongoing', 'is_past', 'is_full', 'duration', 'user_attendance',
            'created_at', 'updated_at'
        ]
    
    def get_user_attendance(self, obj):
        """Get current user's attendance status"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attendance = obj.attendees.filter(user=request.user).first()
            if attendance:
                return attendance.status
        return None


class EventDetailSerializer(EventListSerializer):
    """
    Serializer for event detail view with full information
    """
    attendees = EventAttendeeSerializer(many=True, read_only=True)
    can_register = serializers.SerializerMethodField()
    
    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + ['attendees', 'can_register']
    
    def get_can_register(self, obj):
        """Check if current user can register for event"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_register(request.user)
        return False


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating events
    """
    organizer = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'organizer', 'start_datetime',
            'end_datetime', 'location', 'event_type', 'is_public',
            'max_attendees', 'registration_required', 'cover_image',
            'institution', 'campus', 'tags', 'is_active'
        ]
        read_only_fields = ['id']
    
    def validate(self, attrs):
        """Custom validation for event data"""
        start_datetime = attrs.get('start_datetime')
        end_datetime = attrs.get('end_datetime')
        
        if start_datetime and end_datetime:
            if start_datetime >= end_datetime:
                raise serializers.ValidationError({
                    'end_datetime': 'End date must be after start date.'
                })
            
            # Only validate future dates for new events
            if not self.instance and start_datetime < timezone.now():
                raise serializers.ValidationError({
                    'start_datetime': 'Start date cannot be in the past.'
                })
        
        return attrs


class ClubMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for club member information
    """
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True, required=False)
    is_officer = serializers.BooleanField(read_only=True)
    can_manage_club = serializers.BooleanField(read_only=True)
    membership_duration = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ClubMember
        fields = [
            'id', 'user', 'user_id', 'role', 'joined_at', 'is_officer',
            'can_manage_club', 'membership_duration', 'created_at',
            'updated_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'joined_at', 'is_officer', 'can_manage_club',
            'membership_duration', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        # Set user from context if not provided
        if 'user_id' not in validated_data:
            validated_data['user'] = self.context['request'].user
        else:
            validated_data['user_id'] = validated_data.pop('user_id')
        return super().create(validated_data)


class ClubListSerializer(serializers.ModelSerializer):
    """
    Serializer for club list view with basic information
    """
    president = UserBasicSerializer(read_only=True)
    members_count = serializers.IntegerField(read_only=True)
    officers_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    user_membership = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    
    class Meta:
        model = Club
        fields = [
            'id', 'name', 'description', 'institution', 'campus',
            'category', 'president', 'logo', 'meeting_schedule',
            'contact_email', 'max_members', 'is_public', 'members_count',
            'officers_count', 'is_full', 'user_membership', 'can_join',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'members_count', 'officers_count', 'is_full',
            'user_membership', 'can_join', 'created_at', 'updated_at'
        ]
    
    def get_user_membership(self, obj):
        """Get current user's membership info"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = obj.members.filter(user=request.user, is_active=True).first()
            if membership:
                return {
                    'role': membership.role,
                    'joined_at': membership.joined_at,
                    'can_manage': membership.can_manage_club
                }
        return None
    
    def get_can_join(self, obj):
        """Check if current user can join club"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_join(request.user)
        return False


class ClubDetailSerializer(ClubListSerializer):
    """
    Serializer for club detail view with full information
    """
    members = ClubMemberSerializer(many=True, read_only=True)
    officers = serializers.SerializerMethodField()
    
    class Meta(ClubListSerializer.Meta):
        fields = ClubListSerializer.Meta.fields + ['members', 'officers']
    
    def get_officers(self, obj):
        """Get club officers"""
        officers = obj.get_officers()
        return ClubMemberSerializer(officers, many=True, context=self.context).data


class ClubCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating clubs
    """
    president = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = Club
        fields = [
            'id', 'name', 'description', 'institution', 'campus',
            'category', 'president', 'logo', 'meeting_schedule',
            'contact_email', 'max_members', 'is_public', 'is_active'
        ]
        read_only_fields = ['id']
    
    def validate_name(self, value):
        """Validate club name uniqueness within institution"""
        institution = self.initial_data.get('institution')
        if not institution:
            # If updating, get institution from instance
            if self.instance:
                institution = self.instance.institution.id
        
        if institution:
            queryset = Club.objects.filter(name=value, institution=institution)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError(
                    "A club with this name already exists in this institution."
                )
        
        return value
    
    def create(self, validated_data):
        """Create club and automatically add creator as president member"""
        club = super().create(validated_data)
        
        # Create membership for the president
        ClubMember.objects.create(
            club=club,
            user=club.president,
            role='president'
        )
        
        return club


class AttendanceUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating event attendance status
    """
    status = serializers.ChoiceField(choices=EventAttendee.ATTENDANCE_STATUS)
    
    def validate_status(self, value):
        """Validate attendance status"""
        event = self.context.get('event')
        user = self.context.get('request').user
        
        if value == 'going' and event:
            if event.is_full:
                # Check if user is already registered
                existing_attendance = event.attendees.filter(user=user).first()
                if not existing_attendance or existing_attendance.status != 'going':
                    raise serializers.ValidationError(
                        "Event has reached maximum capacity."
                    )
            
            if not event.is_upcoming:
                raise serializers.ValidationError(
                    "Cannot register for past events."
                )
        
        return value


class ClubMembershipUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating club membership role
    """
    role = serializers.ChoiceField(choices=ClubMember.MEMBER_ROLES)
    
    def validate_role(self, value):
        """Validate role assignment"""
        club = self.context.get('club')
        user_id = self.context.get('user_id')
        request_user = self.context.get('request').user
        
        # Check if request user can manage club
        request_membership = club.members.filter(
            user=request_user, 
            is_active=True
        ).first()
        
        if not request_membership or not request_membership.can_manage_club:
            raise serializers.ValidationError(
                "You don't have permission to manage club memberships."
            )
        
        # Ensure only one president per club
        if value == 'president':
            existing_president = club.members.filter(
                role='president', 
                is_active=True
            ).exclude(user_id=user_id)
            
            if existing_president.exists():
                raise serializers.ValidationError(
                    "Club can only have one president."
                )
        
        return value