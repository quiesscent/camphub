from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

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
    ViewSet for managing events
    """
    permission_classes = [permissions.IsAuthenticated, IsOrganizerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'description', 'location', 'tags']
    ordering_fields = ['start_datetime', 'created_at', 'title']
    ordering = ['-start_datetime']
    
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
    ViewSet for managing clubs
    """
    permission_classes = [permissions.IsAuthenticated, IsClubOfficerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ClubFilter
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['name', 'created_at', 'total_members']
    ordering = ['name']
    
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
