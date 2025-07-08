import django_filters
from django.db import models
from django.utils import timezone
from .models import Event, Club


class EventFilter(django_filters.FilterSet):
    """
    Filter for Event model with various filtering options
    """
    event_type = django_filters.ChoiceFilter(choices=Event.EVENT_TYPES)
    start_date = django_filters.DateFilter(field_name='start_datetime', lookup_expr='date__gte')
    end_date = django_filters.DateFilter(field_name='start_datetime', lookup_expr='date__lte')
    location = django_filters.CharFilter(lookup_expr='icontains')
    is_public = django_filters.BooleanFilter()
    is_upcoming = django_filters.BooleanFilter(method='filter_upcoming')
    is_past = django_filters.BooleanFilter(method='filter_past')
    has_capacity = django_filters.BooleanFilter(method='filter_has_capacity')
    campus = django_filters.UUIDFilter(field_name='campus__id')
    organizer = django_filters.UUIDFilter(field_name='organizer__id')
    tags = django_filters.CharFilter(method='filter_tags')
    
    class Meta:
        model = Event
        fields = [
            'event_type', 'is_public', 'campus', 'organizer',
            'start_date', 'end_date', 'location', 'is_upcoming',
            'is_past', 'has_capacity', 'tags'
        ]
    
    def filter_upcoming(self, queryset, name, value):
        """Filter for upcoming events"""
        if value:
            return queryset.filter(start_datetime__gt=timezone.now())
        return queryset
    
    def filter_past(self, queryset, name, value):
        """Filter for past events"""
        if value:
            return queryset.filter(end_datetime__lt=timezone.now())
        return queryset
    
    def filter_has_capacity(self, queryset, name, value):
        """Filter for events that have available capacity"""
        if value:
            return queryset.filter(
                models.Q(max_attendees__isnull=True) |
                models.Q(max_attendees__gt=models.F('attendees_count'))
            )
        return queryset
    
    def filter_tags(self, queryset, name, value):
        """Filter events by tags"""
        if value:
            # Split by comma for multiple tags
            tags = [tag.strip() for tag in value.split(',')]
            for tag in tags:
                queryset = queryset.filter(tags__icontains=tag)
        return queryset


class ClubFilter(django_filters.FilterSet):
    """
    Filter for Club model with various filtering options
    """
    category = django_filters.ChoiceFilter(choices=Club.CLUB_CATEGORIES)
    campus = django_filters.UUIDFilter(field_name='campus__id')
    president = django_filters.UUIDFilter(field_name='president__id')
    is_public = django_filters.BooleanFilter()
    has_capacity = django_filters.BooleanFilter(method='filter_has_capacity')
    name = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Club
        fields = [
            'category', 'campus', 'president', 'is_public',
            'has_capacity', 'name'
        ]
    
    def filter_has_capacity(self, queryset, name, value):
        """Filter for clubs that have available capacity"""
        if value:
            return queryset.filter(
                models.Q(max_members__isnull=True) |
                models.Q(max_members__gt=models.F('members_count'))
            )
        return queryset