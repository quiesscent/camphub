from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Event, EventAttendee, Club, ClubMember


class EventAttendeeInline(admin.TabularInline):
    """
    Inline admin for event attendees
    """
    model = EventAttendee
    extra = 0
    readonly_fields = ('registered_at', 'created_at', 'updated_at')
    fields = ('user', 'status', 'registered_at', 'is_active')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Admin configuration for Event model
    """
    list_display = [
        'title', 'event_type', 'organizer', 'start_datetime', 
        'location', 'attendees_count', 'is_public', 'is_active'
    ]
    list_filter = [
        'event_type', 'is_public', 'is_active', 'start_datetime',
        'institution', 'campus', 'created_at'
    ]
    search_fields = ['title', 'description', 'location', 'organizer__username']
    readonly_fields = [
        'id', 'attendees_count', 'interested_count', 'is_upcoming',
        'is_ongoing', 'is_past', 'is_full', 'duration', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title', 'description', 'organizer', 'event_type',
                'start_datetime', 'end_datetime', 'location'
            )
        }),
        ('Settings', {
            'fields': (
                'is_public', 'max_attendees', 'registration_required',
                'cover_image', 'tags'
            )
        }),
        ('Institution & Campus', {
            'fields': ('institution', 'campus')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Computed Fields', {
            'fields': (
                'attendees_count', 'interested_count', 'is_upcoming',
                'is_ongoing', 'is_past', 'is_full', 'duration'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [EventAttendeeInline]
    date_hierarchy = 'start_datetime'
    ordering = ['-start_datetime']
    
    actions = ['activate_events', 'deactivate_events', 'make_public', 'make_private']
    
    def attendees_count(self, obj):
        """Display attendees count"""
        count = obj.attendees.filter(status='going', is_active=True).count()
        url = reverse('admin:community_eventattendee_changelist')
        return format_html(
            '<a href="{}?event__id__exact={}&status__exact=going">{}</a>',
            url, obj.id, count
        )
    attendees_count.short_description = 'Going'
    attendees_count.admin_order_field = 'attendees__count'
    
    def activate_events(self, request, queryset):
        """Bulk activate events"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} events were activated.')
    activate_events.short_description = 'Activate selected events'
    
    def deactivate_events(self, request, queryset):
        """Bulk deactivate events"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} events were deactivated.')
    deactivate_events.short_description = 'Deactivate selected events'
    
    def make_public(self, request, queryset):
        """Make events public"""
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} events were made public.')
    make_public.short_description = 'Make selected events public'
    
    def make_private(self, request, queryset):
        """Make events private"""
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} events were made private.')
    make_private.short_description = 'Make selected events private'


@admin.register(EventAttendee)
class EventAttendeeAdmin(admin.ModelAdmin):
    """
    Admin configuration for EventAttendee model
    """
    list_display = ['event', 'user', 'status', 'registered_at', 'is_active']
    list_filter = ['status', 'is_active', 'registered_at', 'event__event_type']
    search_fields = ['event__title', 'user__username', 'user__email']
    readonly_fields = ['registered_at', 'created_at', 'updated_at']
    ordering = ['-registered_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('event', 'user')


class ClubMemberInline(admin.TabularInline):
    """
    Inline admin for club members
    """
    model = ClubMember
    extra = 0
    readonly_fields = ('joined_at', 'created_at', 'updated_at')
    fields = ('user', 'role', 'joined_at', 'is_active')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    """
    Admin configuration for Club model
    """
    list_display = [
        'name', 'category', 'president', 'members_count', 
        'is_public', 'is_active', 'created_at'
    ]
    list_filter = [
        'category', 'is_public', 'is_active', 'institution', 
        'campus', 'created_at'
    ]
    search_fields = ['name', 'description', 'president__username']
    readonly_fields = [
        'id', 'members_count', 'officers_count', 'is_full',
        'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'description', 'category', 'president',
                'meeting_schedule', 'contact_email'
            )
        }),
        ('Settings', {
            'fields': (
                'is_public', 'max_members', 'logo'
            )
        }),
        ('Institution & Campus', {
            'fields': ('institution', 'campus')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Computed Fields', {
            'fields': ('members_count', 'officers_count', 'is_full'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [ClubMemberInline]
    ordering = ['name']
    
    actions = ['activate_clubs', 'deactivate_clubs', 'make_public', 'make_private']
    
    def members_count(self, obj):
        """Display members count"""
        count = obj.members.filter(is_active=True).count()
        url = reverse('admin:community_clubmember_changelist')
        return format_html(
            '<a href="{}?club__id__exact={}">{}</a>',
            url, obj.id, count
        )
    members_count.short_description = 'Members'
    members_count.admin_order_field = 'members__count'
    
    def activate_clubs(self, request, queryset):
        """Bulk activate clubs"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} clubs were activated.')
    activate_clubs.short_description = 'Activate selected clubs'
    
    def deactivate_clubs(self, request, queryset):
        """Bulk deactivate clubs"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} clubs were deactivated.')
    deactivate_clubs.short_description = 'Deactivate selected clubs'
    
    def make_public(self, request, queryset):
        """Make clubs public"""
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} clubs were made public.')
    make_public.short_description = 'Make selected clubs public'
    
    def make_private(self, request, queryset):
        """Make clubs private"""
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} clubs were made private.')
    make_private.short_description = 'Make selected clubs private'


@admin.register(ClubMember)
class ClubMemberAdmin(admin.ModelAdmin):
    """
    Admin configuration for ClubMember model
    """
    list_display = ['club', 'user', 'role', 'joined_at', 'is_active']
    list_filter = ['role', 'is_active', 'joined_at', 'club__category']
    search_fields = ['club__name', 'user__username', 'user__email']
    readonly_fields = ['joined_at', 'created_at', 'updated_at']
    ordering = ['-joined_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('club', 'user')
