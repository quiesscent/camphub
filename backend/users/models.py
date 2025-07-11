from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import EmailValidator
import json
from .utils import OptimizedImageField, process_profile_picture, process_institution_logo, delete_old_image

class Institution(models.Model):
    name = models.CharField(max_length=200, unique=True)
    domain = models.CharField(max_length=100, unique=True, help_text="Email domain for verification (e.g., university.edu)")
    logo = models.ImageField(
        upload_to=OptimizedImageField.save_institution_logo, 
        blank=True, 
        null=True
    )
    address = models.TextField()
    timezone = models.CharField(max_length=50, default='Africa/Nairobi', help_text="Timezone for the institution")
    settings = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Handle logo optimization
        if self.logo and hasattr(self.logo, 'file'):
            # Check if this is a new upload
            if not self.pk or (self.pk and Institution.objects.get(pk=self.pk).logo != self.logo):
                # Delete old logo if updating
                if self.pk:
                    old_instance = Institution.objects.get(pk=self.pk)
                    if old_instance.logo and old_instance.logo != self.logo:
                        delete_old_image(old_instance.logo)
                
                # Process and optimize logo
                self.logo = process_institution_logo(self.logo.file)
        
        super().save(*args, **kwargs)

class Campus(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='campuses')
    name = models.CharField(max_length=200)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['institution__name', 'name']
        unique_together = ['institution', 'name']
        verbose_name_plural = 'Campuses'

    def __str__(self):
        return f"{self.institution.name} - {self.name}"

    @property
    def coordinates(self):
        if self.latitude and self.longitude:
            return {'lat': float(self.latitude), 'lng': float(self.longitude)}
        return None

class User(AbstractUser):
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(
        upload_to=OptimizedImageField.save_profile_picture, 
        blank=True, 
        null=True
    )
    bio = models.TextField(max_length=500, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    major = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False, help_text="Institutional verification status")
    privacy_settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        # Handle profile picture optimization
        if self.profile_picture and hasattr(self.profile_picture, 'file'):
            # Check if this is a new upload
            if not self.pk or (self.pk and User.objects.get(pk=self.pk).profile_picture != self.profile_picture):
                # Delete old profile picture if updating
                if self.pk:
                    old_instance = User.objects.get(pk=self.pk)
                    if old_instance.profile_picture and old_instance.profile_picture != self.profile_picture:
                        delete_old_image(old_instance.profile_picture)
                
                # Process and optimize profile picture
                self.profile_picture = process_profile_picture(self.profile_picture.file)
        
        super().save(*args, **kwargs)

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
    ]
    
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('friends', 'Friends Only'),
        ('private', 'Private'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='user_profiles')
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='user_profiles', null=True, blank=True)
    student_id = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    department = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    dorm_building = models.CharField(max_length=100, blank=True)
    room_number = models.CharField(max_length=20, blank=True)
    privacy_level = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    preferred_content_types = models.JSONField(default=list, blank=True)
    interests = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['institution', 'student_id']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.institution.name}"

    def save(self, *args, **kwargs):
        # Ensure campus belongs to the same institution
        if self.campus and self.campus.institution != self.institution:
            raise ValueError("Campus must belong to the same institution")
        super().save(*args, **kwargs)

    def update_interests(self, tags, weight=1.0):
        """Update user interests based on interaction"""
        for tag in tags:
            if tag in self.interests:
                self.interests[tag] += weight
            else:
                self.interests[tag] = weight
        self.save()