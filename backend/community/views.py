from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from .models import Event, EventAttendee, Club, ClubMember
from .serializers import (
    EventListSerializer, EventDetailSerializer, EventCreateUpdateSerializer,
    EventAttendeeSerializer, AttendanceUpdateSerializer,
    ClubListSerializer, ClubDetailSerializer, ClubCreateUpdateSerializer,
    ClubMemberSerializer, ClubMembershipUpdateSerializer
)
from .permissions import IsOrganizerOrReadOnly, IsClubOfficerOrReadOnly
from .filters import EventFilter, ClubFilter

User = get_user_model()


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing campus events with comprehensive CRUD operations,
    attendance tracking, and advanced filtering capabilities.
    """
    permission_classes = [permissions.IsAuthenticated, IsOrganizerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'description', 'location', 'tags']
    ordering_fields = ['start_datetime', 'created_at', 'title']
    ordering = ['-start_datetime']
    
    @extend_schema(
        description="Get a list of campus events with filtering, search, and pagination. Only shows events from user's institution and public events.",
        parameters=[
            OpenApiParameter(
                name='event_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by event type: academic, social, sports, career, cultural, service',
                required=False,
                enum=['academic', 'social', 'sports', 'career', 'cultural', 'service']
            ),
            OpenApiParameter(
                name='start_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Filter events starting from this date (YYYY-MM-DD)',
                required=False
            ),
            OpenApiParameter(
                name='end_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Filter events ending before this date (YYYY-MM-DD)',
                required=False
            ),
            OpenApiParameter(
                name='location',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search events by location (partial match)',
                required=False
            ),
            OpenApiParameter(
                name='is_upcoming',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter for upcoming events only',
                required=False
            ),
            OpenApiParameter(
                name='is_past',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter for past events only',
                required=False
            ),
            OpenApiParameter(
                name='has_capacity',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter for events with available capacity',
                required=False
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in title, description, location, and tags',
                required=False
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Sort by: start_datetime, created_at, title (use - for descending)',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Events retrieved successfully",
                response=EventListSerializer,
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "count": 25,
                            "next": "http://api.example.com/api/v1/community/events/?page=2",
                            "previous": None,
                            "results": [
                                {
                                    "id": "123e4567-e89b-12d3-a456-426614174000",
                                    "title": "Computer Science Workshop",
                                    "description": "Learn advanced programming techniques",
                                    "organizer": {
                                        "id": 1,
                                        "username": "prof_smith",
                                        "full_name": "Dr. John Smith"
                                    },
                                    "start_datetime": "2024-02-15T14:00:00Z",
                                    "end_datetime": "2024-02-15T17:00:00Z",
                                    "location": "Computer Lab 101",
                                    "event_type": "academic",
                                    "is_public": True,
                                    "max_attendees": 50,
                                    "attendees_count": 23,
                                    "interested_count": 12,
                                    "is_upcoming": True,
                                    "is_full": False,
                                    "user_attendance": "going",
                                    "tags": ["programming", "workshop", "computer-science"],
                                    "created_at": "2024-01-01T10:00:00Z"
                                }
                            ]
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Events']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        description="Create a new campus event. User becomes the organizer automatically.",
        request=EventCreateUpdateSerializer,
        responses={
            201: OpenApiResponse(
                description="Event created successfully",
                response=EventDetailSerializer,
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "title": "New Study Group Meeting",
                            "description": "Weekly study session for advanced mathematics",
                            "organizer": {
                                "id": 1,
                                "username": "student123",
                                "full_name": "Alice Johnson"
                            },
                            "start_datetime": "2024-02-20T19:00:00Z",
                            "end_datetime": "2024-02-20T21:00:00Z",
                            "location": "Library Room 203",
                            "event_type": "academic",
                            "is_public": True,
                            "max_attendees": 15,
                            "registration_required": True,
                            "attendees_count": 1,
                            "interested_count": 0,
                            "is_upcoming": True,
                            "can_register": False,
                            "attendees": [],
                            "tags": ["mathematics", "study-group"],
                            "created_at": "2024-01-01T10:00:00Z"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Validation error",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        value={
                            "start_datetime": ["Start date cannot be in the past"],
                            "end_datetime": ["End date must be after start date"],
                            "max_attendees": ["Must be at least 1"]
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Events'],
        examples=[
            OpenApiExample(
                "Academic Event",
                value={
                    "title": "Advanced Physics Seminar",
                    "description": "Discussion on quantum mechanics and modern physics",
                    "start_datetime": "2024-03-15T14:00:00Z",
                    "end_datetime": "2024-03-15T16:00:00Z",
                    "location": "Physics Building Room 201",
                    "event_type": "academic",
                    "is_public": True,
                    "max_attendees": 30,
                    "registration_required": True,
                    "tags": ["physics", "seminar", "quantum-mechanics"]
                }
            ),
            OpenApiExample(
                "Social Event",
                value={
                    "title": "Campus Movie Night",
                    "description": "Watch the latest blockbuster with fellow students",
                    "start_datetime": "2024-03-22T20:00:00Z",
                    "end_datetime": "2024-03-22T23:00:00Z",
                    "location": "Student Center Auditorium",
                    "event_type": "social",
                    "is_public": True,
                    "max_attendees": 100,
                    "registration_required": False,
                    "tags": ["movie", "social", "entertainment"]
                }
            )
        ]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        description="Get detailed information about a specific event including attendee list and registration status",
        responses={
            200: OpenApiResponse(
                description="Event details retrieved successfully",
                response=EventDetailSerializer
            ),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Event not found")
        },
        tags=['Events']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        description="Update an event (only organizer can update)",
        request=EventCreateUpdateSerializer,
        responses={
            200: OpenApiResponse(
                description="Event updated successfully",
                response=EventDetailSerializer
            ),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not event organizer"),
            404: OpenApiResponse(description="Event not found")
        },
        tags=['Events']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        description="Delete an event (only organizer can delete)",
        responses={
            204: OpenApiResponse(description="Event deleted successfully"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not event organizer"),
            404: OpenApiResponse(description="Event not found")
        },
        tags=['Events']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Filter events based on user's institution and public visibility
        """
        user = self.request.user
        queryset = Event.objects.select_related(
            'organizer', 'institution', 'campus'
        ).prefetch_related(
            Prefetch(
                'attendees',
                queryset=EventAttendee.objects.select_related('user')
            )
        ).annotate(
            total_attendees=Count('attendees', filter=Q(attendees__status='going')),
            total_interested=Count('attendees', filter=Q(attendees__status='interested'))
        )
        
        # Filter by user's institution and public events
        if hasattr(user, 'profile') and user.profile.institution:
            queryset = queryset.filter(
                institution=user.profile.institution,
                is_active=True
            )
            
            # If event is not public, only show to organizer and attendees
            queryset = queryset.filter(
                Q(is_public=True) | 
                Q(organizer=user) | 
                Q(attendees__user=user)
            ).distinct()
        else:
            # If user has no institution, only show public events they organize or attend
            queryset = queryset.filter(
                Q(organizer=user) | Q(attendees__user=user),
                is_active=True
            ).distinct()
        
        return queryset
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        """
        if self.action == 'list':
            return EventListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EventCreateUpdateSerializer
        else:
            return EventDetailSerializer
    
    def perform_create(self, serializer):
        """
        Set organizer and institution when creating event
        """
        user = self.request.user
        institution = None
        campus = None
        
        if hasattr(user, 'profile'):
            institution = user.profile.institution
            campus = user.profile.campus
        
        serializer.save(
            organizer=user,
            institution=institution,
            campus=campus
        )
    
    @extend_schema(
        description="Update user's attendance status for an event. Users can register as 'going', 'interested', or 'not_going'.",
        request=AttendanceUpdateSerializer,
        responses={
            200: OpenApiResponse(
                description="Attendance status updated successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "message": "Attendance status updated to going",
                            "data": {
                                "status": "going",
                                "registered_at": "2024-01-01T10:30:00Z"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Validation error or event full",
                examples=[
                    OpenApiExample(
                        "Event Full",
                        value={
                            "success": False,
                            "errors": {
                                "status": ["Event has reached maximum capacity"]
                            }
                        }
                    ),
                    OpenApiExample(
                        "Past Event",
                        value={
                            "success": False,
                            "errors": {
                                "status": ["Cannot register for past events"]
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Event not found")
        },
        tags=['Event Management'],
        examples=[
            OpenApiExample(
                "Register as Going",
                value={
                    "status": "going"
                }
            ),
            OpenApiExample(
                "Mark as Interested",
                value={
                    "status": "interested"
                }
            ),
            OpenApiExample(
                "Cancel Attendance",
                value={
                    "status": "not_going"
                }
            )
        ]
    )
    @action(detail=True, methods=['put'], 
            serializer_class=AttendanceUpdateSerializer)
    def attend(self, request, pk=None):
        """
        Update user's attendance status for an event
        """
        event = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            context={'event': event, 'request': request}
        )
        
        if serializer.is_valid():
            status_value = serializer.validated_data['status']
            
            # Get or create attendance record
            attendance, created = EventAttendee.objects.get_or_create(
                event=event,
                user=request.user,
                defaults={'status': status_value}
            )
            
            if not created:
                attendance.status = status_value
                attendance.save()
            
            return Response({
                'success': True,
                'message': f'Attendance status updated to {status_value}',
                'data': {
                    'status': status_value,
                    'registered_at': attendance.registered_at
                }
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        description="Get list of event attendees with filtering by attendance status",
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by attendance status: going, interested, not_going',
                required=False,
                enum=['going', 'interested', 'not_going']
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Attendees retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "data": [
                                {
                                    "id": "att-123",
                                    "user": {
                                        "id": 1,
                                        "username": "student123",
                                        "full_name": "Alice Johnson",
                                        "email": "alice@university.edu"
                                    },
                                    "status": "going",
                                    "registered_at": "2024-01-01T10:00:00Z",
                                    "is_active": True
                                }
                            ],
                            "meta": {
                                "total_count": 25,
                                "going_count": 18,
                                "interested_count": 7
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Event not found")
        },
        tags=['Event Management']
    )
    @action(detail=True, methods=['get'])
    def attendees(self, request, pk=None):
        """
        Get list of event attendees
        """
        event = self.get_object()
        attendees = event.attendees.select_related('user').filter(is_active=True)
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            attendees = attendees.filter(status=status_filter)
        
        serializer = EventAttendeeSerializer(attendees, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'total_count': attendees.count(),
                'going_count': event.attendees_count,
                'interested_count': event.interested_count
            }
        })
    
    @extend_schema(
        description="Get events organized by the current user",
        responses={
            200: OpenApiResponse(
                description="User's organized events retrieved successfully",
                response=EventListSerializer
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Event Management']
    )
    @action(detail=False, methods=['get'])
    def my_events(self, request):
        """
        Get events organized by current user
        """
        events = self.get_queryset().filter(organizer=request.user)
        page = self.paginate_queryset(events)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(events, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @extend_schema(
        description="Get events that the current user is attending or interested in",
        responses={
            200: OpenApiResponse(
                description="User's attended events retrieved successfully",
                response=EventListSerializer
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Event Management']
    )
    @action(detail=False, methods=['get'])
    def attending(self, request):
        """
        Get events user is attending or interested in
        """
        events = self.get_queryset().filter(
            attendees__user=request.user,
            attendees__status__in=['going', 'interested']
        )
        
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(events, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class ClubViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing campus clubs and organizations with membership management,
    role-based permissions, and comprehensive filtering capabilities.
    """
    permission_classes = [permissions.IsAuthenticated, IsClubOfficerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ClubFilter
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['name', 'created_at', 'total_members']
    ordering = ['name']
    
    @extend_schema(
        description="Get a list of campus clubs with filtering, search, and pagination. Only shows clubs from user's institution and public clubs.",
        parameters=[
            OpenApiParameter(
                name='category',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by club category',
                required=False,
                enum=['academic', 'social', 'sports', 'cultural', 'professional', 'service', 'hobby', 'religious']
            ),
            OpenApiParameter(
                name='campus',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter by campus ID',
                required=False
            ),
            OpenApiParameter(
                name='has_capacity',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter for clubs with available capacity',
                required=False
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in name, description, and category',
                required=False
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Sort by: name, created_at, total_members (use - for descending)',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Clubs retrieved successfully",
                response=ClubListSerializer,
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "count": 15,
                            "next": None,
                            "previous": None,
                            "results": [
                                {
                                    "id": "123e4567-e89b-12d3-a456-426614174000",
                                    "name": "Computer Science Society",
                                    "description": "A club for CS students to network and learn together",
                                    "category": "academic",
                                    "president": {
                                        "id": 1,
                                        "username": "cs_president",
                                        "full_name": "John Smith"
                                    },
                                    "logo": "/media/clubs/cs_society_logo.jpg",
                                    "meeting_schedule": "Every Wednesday at 6 PM in CS Building Room 101",
                                    "contact_email": "cs.society@university.edu",
                                    "max_members": 100,
                                    "is_public": True,
                                    "members_count": 67,
                                    "officers_count": 5,
                                    "is_full": False,
                                    "user_membership": {
                                        "role": "member",
                                        "joined_at": "2024-01-15T10:00:00Z",
                                        "can_manage": False
                                    },
                                    "can_join": False,
                                    "created_at": "2023-09-01T09:00:00Z"
                                }
                            ]
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Clubs']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        description="Create a new campus club. User automatically becomes the president.",
        request=ClubCreateUpdateSerializer,
        responses={
            201: OpenApiResponse(
                description="Club created successfully",
                response=ClubDetailSerializer,
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "Photography Club",
                            "description": "A club for photography enthusiasts to share and learn",
                            "category": "hobby",
                            "president": {
                                "id": 1,
                                "username": "photo_lover",
                                "full_name": "Alice Johnson"
                            },
                            "meeting_schedule": "Every Friday at 4 PM in Art Building",
                            "contact_email": "photo.club@university.edu",
                            "max_members": 50,
                            "is_public": True,
                            "members_count": 1,
                            "officers_count": 1,
                            "is_full": False,
                            "can_join": False,
                            "members": [
                                {
                                    "id": "mem-123",
                                    "user": {
                                        "id": 1,
                                        "username": "photo_lover",
                                        "full_name": "Alice Johnson"
                                    },
                                    "role": "president",
                                    "joined_at": "2024-01-01T10:00:00Z",
                                    "is_officer": True,
                                    "can_manage_club": True
                                }
                            ],
                            "created_at": "2024-01-01T10:00:00Z"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Validation error",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        value={
                            "name": ["A club with this name already exists in this institution"],
                            "max_members": ["Must be at least 1"],
                            "contact_email": ["Enter a valid email address"]
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Clubs'],
        examples=[
            OpenApiExample(
                "Academic Club",
                value={
                    "name": "Mathematics Study Group",
                    "description": "A club for students interested in advanced mathematics",
                    "category": "academic",
                    "meeting_schedule": "Tuesdays and Thursdays at 7 PM in Math Building Room 205",
                    "contact_email": "math.study@university.edu",
                    "max_members": 25,
                    "is_public": True
                }
            ),
            OpenApiExample(
                "Sports Club",
                value={
                    "name": "Campus Basketball Club",
                    "description": "Competitive and recreational basketball for all skill levels",
                    "category": "sports",
                    "meeting_schedule": "Daily practice at 6 AM in Sports Complex",
                    "contact_email": "basketball@university.edu",
                    "max_members": 30,
                    "is_public": True
                }
            )
        ]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        description="Get detailed information about a specific club including member list and roles",
        responses={
            200: OpenApiResponse(
                description="Club details retrieved successfully",
                response=ClubDetailSerializer
            ),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Club not found")
        },
        tags=['Clubs']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        description="Update a club (only officers and president can update)",
        request=ClubCreateUpdateSerializer,
        responses={
            200: OpenApiResponse(
                description="Club updated successfully",
                response=ClubDetailSerializer
            ),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not club officer"),
            404: OpenApiResponse(description="Club not found")
        },
        tags=['Clubs']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        description="Delete a club (only officers and president can delete)",
        responses={
            204: OpenApiResponse(description="Club deleted successfully"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not club officer"),
            404: OpenApiResponse(description="Club not found")
        },
        tags=['Clubs']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Filter clubs based on user's institution and public visibility
        """
        user = self.request.user
        queryset = Club.objects.select_related(
            'president', 'institution', 'campus'
        ).prefetch_related(
            Prefetch(
                'members',
                queryset=ClubMember.objects.select_related('user').filter(is_active=True)
            )
        ).annotate(
            total_members=Count('members', filter=Q(members__is_active=True)),
            total_officers=Count(
                'members', 
                filter=Q(members__is_active=True, members__role__in=['officer', 'president'])
            )
        )
        
        # Filter by user's institution and public clubs
        if hasattr(user, 'profile') and user.profile.institution:
            queryset = queryset.filter(
                institution=user.profile.institution,
                is_active=True
            )
            
            # If club is not public, only show to members
            queryset = queryset.filter(
                Q(is_public=True) | Q(members__user=user)
            ).distinct()
        else:
            # If user has no institution, only show clubs they're member of
            queryset = queryset.filter(
                members__user=user,
                is_active=True
            ).distinct()
        
        return queryset
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        """
        if self.action == 'list':
            return ClubListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ClubCreateUpdateSerializer
        else:
            return ClubDetailSerializer
    
    def perform_create(self, serializer):
        """
        Set institution when creating club
        """
        user = self.request.user
        institution = None
        campus = None
        
        if hasattr(user, 'profile'):
            institution = user.profile.institution
            campus = user.profile.campus
        
        serializer.save(
            institution=institution,
            campus=campus
        )
    
    @extend_schema(
        description="Join a public club. Private clubs require invitation from officers.",
        responses={
            200: OpenApiResponse(
                description="Successfully joined the club",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "message": "Successfully joined the club",
                            "data": {
                                "id": "mem-123",
                                "user": {
                                    "id": 1,
                                    "username": "student123",
                                    "full_name": "Alice Johnson"
                                },
                                "role": "member",
                                "joined_at": "2024-01-01T10:00:00Z",
                                "is_officer": False,
                                "can_manage_club": False
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Cannot join club",
                examples=[
                    OpenApiExample(
                        "Already Member",
                        value={
                            "success": False,
                            "message": "You are already a member of this club"
                        }
                    ),
                    OpenApiExample(
                        "Club Full",
                        value={
                            "success": False,
                            "message": "Cannot join this club"
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Club not found")
        },
        tags=['Club Management']
    )
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """
        Join a club
        """
        club = self.get_object()
        
        if not club.can_join(request.user):
            return Response({
                'success': False,
                'message': 'Cannot join this club'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        membership, created = ClubMember.objects.get_or_create(
            club=club,
            user=request.user,
            defaults={'role': 'member'}
        )
        
        if created:
            return Response({
                'success': True,
                'message': 'Successfully joined the club',
                'data': ClubMemberSerializer(membership).data
            })
        else:
            # Reactivate if previously inactive
            if not membership.is_active:
                membership.is_active = True
                membership.save()
                return Response({
                    'success': True,
                    'message': 'Successfully rejoined the club',
                    'data': ClubMemberSerializer(membership).data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'You are already a member of this club'
                }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        description="Leave a club. Presidents must transfer leadership before leaving.",
        responses={
            200: OpenApiResponse(
                description="Successfully left the club",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "message": "Successfully left the club"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Cannot leave club",
                examples=[
                    OpenApiExample(
                        "President Cannot Leave",
                        value={
                            "success": False,
                            "message": "Presidents must transfer leadership before leaving"
                        }
                    ),
                    OpenApiExample(
                        "Not Member",
                        value={
                            "success": False,
                            "message": "You are not a member of this club"
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Club not found")
        },
        tags=['Club Management']
    )
    @action(detail=True, methods=['delete'])
    def leave(self, request, pk=None):
        """
        Leave a club
        """
        club = self.get_object()
        
        try:
            membership = ClubMember.objects.get(
                club=club,
                user=request.user,
                is_active=True
            )
            
            # Presidents cannot leave unless they transfer leadership
            if membership.role == 'president':
                return Response({
                    'success': False,
                    'message': 'Presidents must transfer leadership before leaving'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            membership.is_active = False
            membership.save()
            
            return Response({
                'success': True,
                'message': 'Successfully left the club'
            })
            
        except ClubMember.DoesNotExist:
            return Response({
                'success': False,
                'message': 'You are not a member of this club'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        description="Get list of club members with optional role filtering",
        parameters=[
            OpenApiParameter(
                name='role',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by member role: member, officer, president',
                required=False,
                enum=['member', 'officer', 'president']
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Members retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "data": [
                                {
                                    "id": "mem-123",
                                    "user": {
                                        "id": 1,
                                        "username": "student123",
                                        "full_name": "Alice Johnson",
                                        "email": "alice@university.edu"
                                    },
                                    "role": "president",
                                    "joined_at": "2023-09-01T10:00:00Z",
                                    "is_officer": True,
                                    "can_manage_club": True,
                                    "membership_duration": 120
                                }
                            ],
                            "meta": {
                                "total_count": 67,
                                "members_count": 60,
                                "officers_count": 7
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Club not found")
        },
        tags=['Club Management']
    )
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """
        Get list of club members
        """
        club = self.get_object()
        members = club.members.select_related('user').filter(is_active=True)
        
        # Filter by role if provided
        role_filter = request.query_params.get('role')
        if role_filter:
            members = members.filter(role=role_filter)
        
        serializer = ClubMemberSerializer(members, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'total_count': members.count(),
                'members_count': club.members_count,
                'officers_count': club.officers_count
            }
        })
    
    @extend_schema(
        description="Update a member's role in the club. Only officers and president can manage roles.",
        request=ClubMembershipUpdateSerializer,
        responses={
            200: OpenApiResponse(
                description="Member role updated successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "success": True,
                            "message": "Role updated to officer",
                            "data": {
                                "id": "mem-123",
                                "user": {
                                    "id": 2,
                                    "username": "student456",
                                    "full_name": "Bob Wilson"
                                },
                                "role": "officer",
                                "joined_at": "2023-10-15T10:00:00Z",
                                "is_officer": True,
                                "can_manage_club": True
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Validation error",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        value={
                            "success": False,
                            "errors": {
                                "role": ["Club can only have one president"]
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied - not club officer"),
            404: OpenApiResponse(description="Club or member not found")
        },
        tags=['Club Management'],
        examples=[
            OpenApiExample(
                "Promote to Officer",
                value={
                    "role": "officer"
                }
            ),
            OpenApiExample(
                "Transfer Presidency",
                value={
                    "role": "president"
                }
            ),
            OpenApiExample(
                "Demote to Member",
                value={
                    "role": "member"
                }
            )
        ]
    )
    @action(detail=True, methods=['put'], url_path='members/(?P<user_id>[^/.]+)')
    def update_member_role(self, request, pk=None, user_id=None):
        """
        Update a member's role in the club
        """
        club = self.get_object()
        
        try:
            member = ClubMember.objects.get(
                club=club,
                user_id=user_id,
                is_active=True
            )
        except ClubMember.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Member not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ClubMembershipUpdateSerializer(
            data=request.data,
            context={
                'club': club,
                'user_id': user_id,
                'request': request
            }
        )
        
        if serializer.is_valid():
            new_role = serializer.validated_data['role']
            
            # If promoting to president, demote current president
            if new_role == 'president':
                current_president = ClubMember.objects.filter(
                    club=club,
                    role='president',
                    is_active=True
                ).exclude(user_id=user_id).first()
                
                if current_president:
                    current_president.role = 'officer'
                    current_president.save()
            
            member.role = new_role
            member.save()
            
            return Response({
                'success': True,
                'message': f'Role updated to {new_role}',
                'data': ClubMemberSerializer(member).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        description="Get clubs where the current user is a member",
        responses={
            200: OpenApiResponse(
                description="User's club memberships retrieved successfully",
                response=ClubListSerializer
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Club Management']
    )
    @action(detail=False, methods=['get'])
    def my_clubs(self, request):
        """
        Get clubs where user is a member
        """
        clubs = self.get_queryset().filter(
            members__user=request.user,
            members__is_active=True
        )
        
        page = self.paginate_queryset(clubs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(clubs, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @extend_schema(
        description="Get clubs where the current user is an officer or president",
        responses={
            200: OpenApiResponse(
                description="User's managed clubs retrieved successfully",
                response=ClubListSerializer
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Club Management']
    )
    @action(detail=False, methods=['get'])
    def managing(self, request):
        """
        Get clubs where user is an officer or president
        """
        clubs = self.get_queryset().filter(
            members__user=request.user,
            members__role__in=['officer', 'president'],
            members__is_active=True
        )
        
        page = self.paginate_queryset(clubs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(clubs, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
