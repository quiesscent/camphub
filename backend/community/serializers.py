from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import RegexValidator, EmailValidator
from .models import Event, EventAttendee, Club, ClubMember

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for nested representations in community features
    """
    full_name = serializers.CharField(
        source='get_full_name', 
        read_only=True,
        help_text="User's full name (first name + last name)"
    )
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email']
        read_only_fields = ['id', 'username', 'full_name', 'email']
        
    username = serializers.CharField(
        read_only=True,
        help_text="Unique username for identification"
    )
    email = serializers.EmailField(
        read_only=True,
        help_text="User's institutional email address"
    )


class EventAttendeeSerializer(serializers.ModelSerializer):
    """
    Serializer for event attendee information with user details
    """
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.UUIDField(
        write_only=True,
        required=False,
        help_text="ID of the user to add as attendee (optional, defaults to current user)",
        error_messages={
            'invalid': 'Invalid user ID format'
        }
    )
    
    class Meta:
        model = EventAttendee
        fields = [
            'id', 'user', 'user_id', 'status', 'registered_at',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'registered_at', 'created_at', 'updated_at']
        
    status = serializers.ChoiceField(
        choices=EventAttendee.ATTENDANCE_STATUS,
        help_text="Attendance status: going (confirmed), interested (maybe), not_going (declined)",
        error_messages={
            'required': 'Attendance status is required',
            'invalid_choice': 'Status must be one of: going, interested, not_going'
        }
    )
    registered_at = serializers.DateTimeField(
        read_only=True,
        help_text="Timestamp when the user registered for the event"
    )
    is_active = serializers.BooleanField(
        read_only=True,
        help_text="Whether this attendance record is active"
    )
    
    def create(self, validated_data):
        # Set user from context if not provided
        if 'user_id' not in validated_data:
            validated_data['user'] = self.context['request'].user
        else:
            validated_data['user_id'] = validated_data.pop('user_id')
        return super().create(validated_data)


class EventListSerializer(serializers.ModelSerializer):
    """
    Serializer for event list view with essential information and computed fields
    """
    organizer = UserBasicSerializer(read_only=True)
    attendees_count = serializers.IntegerField(
        read_only=True,
        help_text="Number of users confirmed as going"
    )
    interested_count = serializers.IntegerField(
        read_only=True,
        help_text="Number of users marked as interested"
    )
    is_upcoming = serializers.BooleanField(
        read_only=True,
        help_text="Whether the event is in the future"
    )
    is_ongoing = serializers.BooleanField(
        read_only=True,
        help_text="Whether the event is currently happening"
    )
    is_past = serializers.BooleanField(
        read_only=True,
        help_text="Whether the event has ended"
    )
    is_full = serializers.BooleanField(
        read_only=True,
        help_text="Whether the event has reached maximum capacity"
    )
    duration = serializers.FloatField(
        read_only=True,
        help_text="Event duration in minutes"
    )
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
        
    title = serializers.CharField(
        read_only=True,
        help_text="Event title/name"
    )
    description = serializers.CharField(
        read_only=True,
        help_text="Detailed description of the event"
    )
    start_datetime = serializers.DateTimeField(
        read_only=True,
        help_text="Event start date and time in ISO format"
    )
    end_datetime = serializers.DateTimeField(
        read_only=True,
        help_text="Event end date and time in ISO format"
    )
    location = serializers.CharField(
        read_only=True,
        help_text="Event location (room, building, address)"
    )
    event_type = serializers.ChoiceField(
        choices=Event.EVENT_TYPES,
        read_only=True,
        help_text="Type of event: academic, social, sports, career, cultural, service"
    )
    is_public = serializers.BooleanField(
        read_only=True,
        help_text="Whether the event is open to all users or restricted"
    )
    max_attendees = serializers.IntegerField(
        read_only=True,
        help_text="Maximum number of attendees (null for unlimited)"
    )
    registration_required = serializers.BooleanField(
        read_only=True,
        help_text="Whether users must register to attend"
    )
    tags = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        help_text="List of tags for categorizing and searching the event"
    )
    
    def get_user_attendance(self, obj):
        """Get current user's attendance status for this event"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attendance = obj.attendees.filter(user=request.user).first()
            if attendance:
                return attendance.status
        return None


class EventDetailSerializer(EventListSerializer):
    """
    Serializer for event detail view with complete information including attendee list
    """
    attendees = EventAttendeeSerializer(many=True, read_only=True)
    can_register = serializers.SerializerMethodField()
    
    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + ['attendees', 'can_register']
        
    attendees = EventAttendeeSerializer(
        many=True,
        read_only=True,
        help_text="List of all event attendees with their status"
    )
    can_register = serializers.BooleanField(
        read_only=True,
        help_text="Whether the current user can register for this event"
    )
    
    def get_can_register(self, obj):
        """Check if current user can register for this event"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_register(request.user)
        return False


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating events with comprehensive validation
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
        
    title = serializers.CharField(
        max_length=200,
        help_text="Event title (2-200 characters)",
        error_messages={
            'required': 'Event title is required',
            'blank': 'Event title cannot be empty',
            'max_length': 'Event title cannot exceed 200 characters'
        }
    )
    description = serializers.CharField(
        help_text="Detailed description of the event, its purpose, and what attendees can expect",
        error_messages={
            'required': 'Event description is required',
            'blank': 'Event description cannot be empty'
        }
    )
    start_datetime = serializers.DateTimeField(
        help_text="Event start date and time in ISO format (YYYY-MM-DDTHH:MM:SSZ)",
        error_messages={
            'required': 'Start date and time is required',
            'invalid': 'Enter a valid date and time in ISO format'
        }
    )
    end_datetime = serializers.DateTimeField(
        help_text="Event end date and time in ISO format (YYYY-MM-DDTHH:MM:SSZ)",
        error_messages={
            'required': 'End date and time is required',
            'invalid': 'Enter a valid date and time in ISO format'
        }
    )
    location = serializers.CharField(
        max_length=200,
        help_text="Event location (room number, building name, or full address)",
        error_messages={
            'required': 'Event location is required',
            'blank': 'Event location cannot be empty',
            'max_length': 'Location cannot exceed 200 characters'
        }
    )
    event_type = serializers.ChoiceField(
        choices=Event.EVENT_TYPES,
        help_text="Type of event: academic, social, sports, career, cultural, service",
        error_messages={
            'required': 'Event type is required',
            'invalid_choice': 'Event type must be one of: academic, social, sports, career, cultural, service'
        }
    )
    is_public = serializers.BooleanField(
        default=True,
        help_text="Whether the event is open to all users (true) or restricted to specific groups (false)"
    )
    max_attendees = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        help_text="Maximum number of attendees (leave empty for unlimited capacity)",
        error_messages={
            'min_value': 'Maximum attendees must be at least 1',
            'invalid': 'Enter a valid number'
        }
    )
    registration_required = serializers.BooleanField(
        default=False,
        help_text="Whether users must register in advance to attend the event"
    )
    cover_image = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Optional cover image for the event (JPEG, PNG, max 5MB)",
        error_messages={
            'invalid_image': 'Upload a valid image file (JPEG, PNG)'
        }
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
        help_text="List of tags for categorizing the event (max 10 tags, 50 chars each)",
        error_messages={
            'invalid': 'Tags must be a list of strings'
        }
    )
    
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
        
        # Validate tags
        tags = attrs.get('tags', [])
        if len(tags) > 10:
            raise serializers.ValidationError({
                'tags': 'Maximum 10 tags allowed.'
            })
        
        return attrs


class ClubMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for club member information with user details and computed fields
    """
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.UUIDField(
        write_only=True,
        required=False,
        help_text="ID of the user to add as member (optional, defaults to current user)",
        error_messages={
            'invalid': 'Invalid user ID format'
        }
    )
    is_officer = serializers.BooleanField(
        read_only=True,
        help_text="Whether this member has officer or president privileges"
    )
    can_manage_club = serializers.BooleanField(
        read_only=True,
        help_text="Whether this member can manage club settings and members"
    )
    membership_duration = serializers.IntegerField(
        read_only=True,
        help_text="Number of days since joining the club"
    )
    
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
        
    role = serializers.ChoiceField(
        choices=ClubMember.MEMBER_ROLES,
        help_text="Member role: member (regular), officer (can manage), president (full control)",
        error_messages={
            'required': 'Member role is required',
            'invalid_choice': 'Role must be one of: member, officer, president'
        }
    )
    joined_at = serializers.DateTimeField(
        read_only=True,
        help_text="Timestamp when the user joined the club"
    )
    is_active = serializers.BooleanField(
        read_only=True,
        help_text="Whether this membership is currently active"
    )
    
    def create(self, validated_data):
        # Set user from context if not provided
        if 'user_id' not in validated_data:
            validated_data['user'] = self.context['request'].user
        else:
            validated_data['user_id'] = validated_data.pop('user_id')
        return super().create(validated_data)


class ClubListSerializer(serializers.ModelSerializer):
    """
    Serializer for club list view with essential information and membership status
    """
    president = UserBasicSerializer(read_only=True)
    members_count = serializers.IntegerField(
        read_only=True,
        help_text="Total number of active members"
    )
    officers_count = serializers.IntegerField(
        read_only=True,
        help_text="Number of officers and president"
    )
    is_full = serializers.BooleanField(
        read_only=True,
        help_text="Whether the club has reached maximum capacity"
    )
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
        
    name = serializers.CharField(
        read_only=True,
        help_text="Club name"
    )
    description = serializers.CharField(
        read_only=True,
        help_text="Detailed description of the club's purpose and activities"
    )
    category = serializers.ChoiceField(
        choices=Club.CLUB_CATEGORIES,
        read_only=True,
        help_text="Club category: academic, social, sports, cultural, professional, service, hobby, religious"
    )
    meeting_schedule = serializers.CharField(
        read_only=True,
        help_text="Regular meeting schedule and location"
    )
    contact_email = serializers.EmailField(
        read_only=True,
        help_text="Official contact email for the club"
    )
    max_members = serializers.IntegerField(
        read_only=True,
        help_text="Maximum number of members allowed (null for unlimited)"
    )
    is_public = serializers.BooleanField(
        read_only=True,
        help_text="Whether the club is open for anyone to join"
    )
    
    def get_user_membership(self, obj):
        """Get current user's membership information for this club"""
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
        """Check if current user can join this club"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_join(request.user)
        return False


class ClubDetailSerializer(ClubListSerializer):
    """
    Serializer for club detail view with complete member list and officer information
    """
    members = ClubMemberSerializer(many=True, read_only=True)
    officers = serializers.SerializerMethodField()
    
    class Meta(ClubListSerializer.Meta):
        fields = ClubListSerializer.Meta.fields + ['members', 'officers']
        
    members = ClubMemberSerializer(
        many=True,
        read_only=True,
        help_text="Complete list of active club members with their roles"
    )
    officers = serializers.ListField(
        child=ClubMemberSerializer(),
        read_only=True,
        help_text="List of club officers and president"
    )
    
    def get_officers(self, obj):
        """Get list of club officers and president"""
        officers = obj.get_officers()
        return ClubMemberSerializer(officers, many=True, context=self.context).data


class ClubCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating clubs with comprehensive validation
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
        
    name = serializers.CharField(
        max_length=200,
        help_text="Club name (2-200 characters, must be unique within institution)",
        error_messages={
            'required': 'Club name is required',
            'blank': 'Club name cannot be empty',
            'max_length': 'Club name cannot exceed 200 characters'
        }
    )
    description = serializers.CharField(
        help_text="Detailed description of the club's purpose, activities, and goals",
        error_messages={
            'required': 'Club description is required',
            'blank': 'Club description cannot be empty'
        }
    )
    category = serializers.ChoiceField(
        choices=Club.CLUB_CATEGORIES,
        help_text="Club category: academic, social, sports, cultural, professional, service, hobby, religious",
        error_messages={
            'required': 'Club category is required',
            'invalid_choice': 'Category must be one of: academic, social, sports, cultural, professional, service, hobby, religious'
        }
    )
    logo = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Optional club logo (JPEG, PNG, max 5MB)",
        error_messages={
            'invalid_image': 'Upload a valid image file (JPEG, PNG)'
        }
    )
    meeting_schedule = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Regular meeting schedule and location (e.g., 'Every Tuesday at 7 PM in Room 101')",
        error_messages={
            'max_length': 'Meeting schedule cannot exceed 500 characters'
        }
    )
    contact_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        validators=[EmailValidator()],
        help_text="Official contact email for the club",
        error_messages={
            'invalid': 'Enter a valid email address'
        }
    )
    max_members = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        help_text="Maximum number of members allowed (leave empty for unlimited)",
        error_messages={
            'min_value': 'Maximum members must be at least 1',
            'invalid': 'Enter a valid number'
        }
    )
    is_public = serializers.BooleanField(
        default=True,
        help_text="Whether the club is open for anyone to join (true) or invitation-only (false)"
    )
    
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
    Serializer for updating event attendance status with validation
    """
    status = serializers.ChoiceField(
        choices=EventAttendee.ATTENDANCE_STATUS,
        help_text="Attendance status: going (confirmed attendance), interested (maybe attending), not_going (declined)",
        error_messages={
            'required': 'Attendance status is required',
            'invalid_choice': 'Status must be one of: going, interested, not_going'
        }
    )
    
    def validate_status(self, value):
        """Validate attendance status based on event constraints"""
        event = self.context.get('event')
        user = self.context.get('request').user
        
        if value == 'going' and event:
            if event.is_full:
                # Check if user is already registered as going
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
    Serializer for updating club membership roles with permission validation
    """
    role = serializers.ChoiceField(
        choices=ClubMember.MEMBER_ROLES,
        help_text="New role for the member: member (regular), officer (can manage), president (full control)",
        error_messages={
            'required': 'Role is required',
            'invalid_choice': 'Role must be one of: member, officer, president'
        }
    )
    
    def validate_role(self, value):
        """Validate role assignment based on permissions and constraints"""
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
                    "Club can only have one president. Current president will be demoted to officer."
                )
        
        return value