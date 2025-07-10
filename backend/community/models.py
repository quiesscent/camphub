from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid

User = get_user_model()

class BaseModel(models.Model):
    """
    Abstract base model with common fields
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

class EventQuerySet(models.QuerySet):
    """
    Custom QuerySet for Event model
    """
    def active(self):
        return self.filter(is_active=True)
    
    def public(self):
        return self.filter(is_public=True)
    
    def upcoming(self):
        return self.filter(start_datetime__gte=timezone.now())
    
    def past(self):
        return self.filter(end_datetime__lt=timezone.now())
    
    def by_type(self, event_type):
        return self.filter(event_type=event_type)
    
    def by_institution(self, institution):
        return self.filter(institution=institution)
    
    def by_campus(self, campus):
        return self.filter(campus=campus)

class EventManager(models.Manager):
    """
    Custom Manager for Event model
    """
    def get_queryset(self):
        return EventQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def public(self):
        return self.get_queryset().public()
    
    def upcoming(self):
        return self.get_queryset().upcoming()
    
    def past(self):
        return self.get_queryset().past()
    
    def by_type(self, event_type):
        return self.get_queryset().by_type(event_type)

class Event(BaseModel):
    """
    Model for campus events
    """
    EVENT_TYPES = [
        ('academic', _('Academic')),
        ('social', _('Social')),
        ('sports', _('Sports')),
        ('career', _('Career')),
        ('cultural', _('Cultural')),
        ('service', _('Service')),
    ]
    
    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    organizer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='organized_events'
    )
    start_datetime = models.DateTimeField(db_index=True)
    end_datetime = models.DateTimeField(db_index=True)
    location = models.CharField(max_length=200)
    event_type = models.CharField(
        max_length=20, 
        choices=EVENT_TYPES, 
        default='academic',
        db_index=True
    )
    is_public = models.BooleanField(default=True)
    max_attendees = models.PositiveIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1)]
    )
    registration_required = models.BooleanField(default=False)
    cover_image = models.ImageField(
        upload_to='events/covers/', 
        null=True, 
        blank=True
    )
    # Assuming Institution and Campus models exist in another app
    institution = models.ForeignKey(
        'users.Institution',  # Adjust based on your app structure
        on_delete=models.CASCADE,
        related_name='events'
    )
    campus = models.ForeignKey(
        'users.Campus',  # Adjust based on your app structure
        on_delete=models.CASCADE,
        related_name='events',
        null=True,
        blank=True
    )
    tags = models.JSONField(default=list, blank=True)
    
    objects = EventManager()
    
    class Meta:
        db_table = 'community_events'
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['start_datetime', 'end_datetime']),
            models.Index(fields=['institution', 'event_type']),
            models.Index(fields=['is_public', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"
    
    def clean(self):
        """
        Custom validation for the model
        """
        super().clean()
        
        if self.start_datetime and self.end_datetime:
            if self.start_datetime >= self.end_datetime:
                raise ValidationError({
                    'end_datetime': _('End date must be after start date.')
                })
            
            if self.start_datetime < timezone.now():
                raise ValidationError({
                    'start_datetime': _('Start date cannot be in the past.')
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_upcoming(self):
        """Check if event is upcoming"""
        if not self.start_datetime:
            return False
        return self.start_datetime > timezone.now()
    
    @property
    def is_ongoing(self):
        """Check if event is currently happening"""
        if not self.start_datetime or not self.end_datetime:
            return False
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime
    
    @property
    def is_past(self):
        """Check if event has ended"""
        if not self.end_datetime:
            return False
        return self.end_datetime < timezone.now()
    
    @property
    def duration(self):
        """Get event duration in minutes"""
        if self.start_datetime and self.end_datetime:
            return (self.end_datetime - self.start_datetime).total_seconds() / 60
        return 0
    
    @property
    def attendees_count(self):
        """Get total number of attendees"""
        return self.attendees.filter(status='going').count()
    
    @property
    def interested_count(self):
        """Get number of interested users"""
        return self.attendees.filter(status='interested').count()
    
    @property
    def is_full(self):
        """Check if event has reached capacity"""
        if self.max_attendees:
            return self.attendees_count >= self.max_attendees
        return False
    
    def can_register(self, user):
        """Check if user can register for event"""
        if not self.is_upcoming:
            return False
        if self.is_full:
            return False
        if self.attendees.filter(user=user).exists():
            return False
        return True
    
    def add_tag(self, tag):
        """Add a tag to the event"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.save(update_fields=['tags'])
    
    def remove_tag(self, tag):
        """Remove a tag from the event"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.save(update_fields=['tags'])

class EventAttendee(BaseModel):
    """
    Model for event attendance tracking
    """
    ATTENDANCE_STATUS = [
        ('going', _('Going')),
        ('interested', _('Interested')),
        ('not_going', _('Not Going')),
    ]
    
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name='attendees'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='event_attendances'
    )
    status = models.CharField(
        max_length=20, 
        choices=ATTENDANCE_STATUS, 
        default='interested'
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'community_event_attendees'
        verbose_name = _('Event Attendee')
        verbose_name_plural = _('Event Attendees')
        unique_together = ['event', 'user']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['user', 'registered_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.event.title} ({self.status})"
    
    def clean(self):
        """
        Custom validation for attendance
        """
        super().clean()
        
        if self.event and self.status == 'going':
            if self.event.is_full and not self.pk:
                raise ValidationError({
                    'status': _('Event has reached maximum capacity.')
                })
            
            if not self.event.is_upcoming:
                raise ValidationError({
                    'status': _('Cannot register for past events.')
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class ClubQuerySet(models.QuerySet):
    """
    Custom QuerySet for Club model
    """
    def active(self):
        return self.filter(is_active=True)
    
    def public(self):
        return self.filter(is_public=True)
    
    def by_category(self, category):
        return self.filter(category=category)
    
    def by_institution(self, institution):
        return self.filter(institution=institution)
    
    def by_campus(self, campus):
        return self.filter(campus=campus)

class ClubManager(models.Manager):
    """
    Custom Manager for Club model
    """
    def get_queryset(self):
        return ClubQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def public(self):
        return self.get_queryset().public()
    
    def by_category(self, category):
        return self.get_queryset().by_category(category)

class Club(BaseModel):
    """
    Model for campus clubs and organizations
    """
    CLUB_CATEGORIES = [
        ('academic', _('Academic')),
        ('social', _('Social')),
        ('sports', _('Sports')),
        ('cultural', _('Cultural')),
        ('professional', _('Professional')),
        ('service', _('Service')),
        ('hobby', _('Hobby')),
        ('religious', _('Religious')),
    ]
    
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    institution = models.ForeignKey(
        'users.Institution',  # Adjust based on your app structure
        on_delete=models.CASCADE,
        related_name='clubs'
    )
    campus = models.ForeignKey(
        'users.Campus',  # Adjust based on your app structure
        on_delete=models.CASCADE,
        related_name='clubs',
        null=True,
        blank=True
    )
    category = models.CharField(
        max_length=20, 
        choices=CLUB_CATEGORIES, 
        default='social',
        db_index=True
    )
    president = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='clubs_as_president'
    )
    logo = models.ImageField(
        upload_to='clubs/logos/', 
        null=True, 
        blank=True
    )
    meeting_schedule = models.CharField(
        max_length=500, 
        null=True, 
        blank=True,
        help_text=_('e.g., "Every Tuesday at 7 PM in Room 101"')
    )
    contact_email = models.EmailField(null=True, blank=True)
    max_members = models.PositiveIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1)]
    )
    is_public = models.BooleanField(default=True)
    
    objects = ClubManager()
    
    class Meta:
        db_table = 'community_clubs'
        verbose_name = _('Club')
        verbose_name_plural = _('Clubs')
        ordering = ['name']
        unique_together = ['name', 'institution']
        indexes = [
            models.Index(fields=['institution', 'category']),
            models.Index(fields=['is_public', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def members_count(self):
        """Get total number of active members"""
        return self.members.filter(is_active=True).count()
    
    @property
    def officers_count(self):
        """Get number of officers"""
        return self.members.filter(
            role__in=['officer', 'president'], 
            is_active=True
        ).count()
    
    @property
    def is_full(self):
        """Check if club has reached capacity"""
        if self.max_members:
            return self.members_count >= self.max_members
        return False
    
    def can_join(self, user):
        """Check if user can join club"""
        if self.is_full:
            return False
        if self.members.filter(user=user, is_active=True).exists():
            return False
        return True
    
    def get_officers(self):
        """Get all officers"""
        return self.members.filter(
            role__in=['officer', 'president'],
            is_active=True
        ).select_related('user')
    
    def get_members(self):
        """Get all active members"""
        return self.members.filter(is_active=True).select_related('user')

class ClubMember(BaseModel):
    """
    Model for club membership
    """
    MEMBER_ROLES = [
        ('member', _('Member')),
        ('officer', _('Officer')),
        ('president', _('President')),
    ]
    
    club = models.ForeignKey(
        Club, 
        on_delete=models.CASCADE, 
        related_name='members'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='club_memberships'
    )
    role = models.CharField(
        max_length=20, 
        choices=MEMBER_ROLES, 
        default='member'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'community_club_members'
        verbose_name = _('Club Member')
        verbose_name_plural = _('Club Members')
        unique_together = ['club', 'user']
        indexes = [
            models.Index(fields=['club', 'role']),
            models.Index(fields=['user', 'joined_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.club.name} ({self.role})"
    
    def clean(self):
        """
        Custom validation for club membership
        """
        super().clean()
        
        if self.club and self.club.is_full and not self.pk:
            raise ValidationError({
                'club': _('Club has reached maximum capacity.')
            })
        
        # Ensure only one president per club
        if self.role == 'president':
            existing_president = ClubMember.objects.filter(
                club=self.club, 
                role='president', 
                is_active=True
            ).exclude(pk=self.pk)
            
            if existing_president.exists():
                raise ValidationError({
                    'role': _('Club can only have one president.')
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Update club president if this member becomes president
        if self.role == 'president' and self.is_active:
            self.club.president = self.user
            self.club.save(update_fields=['president'])
    
    @property
    def is_officer(self):
        """Check if member is an officer or president"""
        return self.role in ['officer', 'president']
    
    @property
    def can_manage_club(self):
        """Check if member can manage club settings"""
        return self.role in ['officer', 'president'] and self.is_active
    
    @property
    def membership_duration(self):
        """Get membership duration in days"""
        return (timezone.now() - self.joined_at).days

# Signal handlers for maintaining data integrity
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=ClubMember)
def update_club_president(sender, instance, created, **kwargs):
    """
    Update club president when a member becomes president
    """
    if instance.role == 'president' and instance.is_active:
        Club.objects.filter(pk=instance.club.pk).update(president=instance.user)

@receiver(post_delete, sender=ClubMember)
def handle_president_deletion(sender, instance, **kwargs):
    """
    Handle president deletion - assign new president if needed
    """
    if instance.role == 'president':
        # Find next officer to promote
        next_officer = ClubMember.objects.filter(
            club=instance.club,
            role='officer',
            is_active=True
        ).first()
        
        if next_officer:
            next_officer.role = 'president'
            next_officer.save()
        else:
            # If no officers, promote longest-serving member
            longest_member = ClubMember.objects.filter(
                club=instance.club,
                is_active=True
            ).order_by('joined_at').first()
            
            if longest_member:
                longest_member.role = 'president'
                longest_member.save()