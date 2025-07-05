from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.db import models
from .models import Course, CourseEnrollment, StudyGroup, StudyGroupMember


class CourseEnrollmentInline(admin.TabularInline):
    """Inline admin for course enrollments"""
    model = CourseEnrollment
    extra = 0
    fields = ('user', 'role', 'enrollment_date', 'is_active', 'grade')
    readonly_fields = ('enrollment_date',)
    raw_id_fields = ('user',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


class StudyGroupInline(admin.TabularInline):
    """Inline admin for study groups"""
    model = StudyGroup
    extra = 0
    fields = ('name', 'creator', 'max_members', 'is_private', 'is_active')
    readonly_fields = ('creator',)
    raw_id_fields = ('creator',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin interface for Course model"""
    list_display = (
        'course_code', 'course_name', 'instructor', 'institution', 
        'semester_year', 'enrollment_count', 'study_groups_count', 'is_active'
    )
    list_filter = (
        'semester', 'year', 'institution', 'is_active', 
        'enrollment_open', 'created_at'
    )
    search_fields = (
        'course_code', 'course_name', 'instructor__first_name', 
        'instructor__last_name', 'instructor__email'
    )
    raw_id_fields = ('instructor',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-year', 'semester', 'course_code')
    inlines = [CourseEnrollmentInline, StudyGroupInline]
    
    fieldsets = (
        ('Course Information', {
            'fields': ('institution', 'course_code', 'course_name', 'description')
        }),
        ('Academic Period', {
            'fields': ('semester', 'year')
        }),
        ('Staff', {
            'fields': ('instructor',)
        }),
        ('Settings', {
            'fields': ('max_enrollment', 'enrollment_open', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_courses', 'deactivate_courses', 'open_enrollment', 'close_enrollment']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'institution', 'instructor'
        ).annotate(
            enrollment_count=Count('enrollments', filter=models.Q(enrollments__is_active=True)),
            study_groups_count=Count('study_groups', filter=models.Q(study_groups__is_active=True))
        )
    
    def semester_year(self, obj):
        """Display semester and year combined"""
        return f"{obj.get_semester_display()} {obj.year}"
    semester_year.short_description = 'Semester'
    semester_year.admin_order_field = 'year'
    
    def enrollment_count(self, obj):
        """Display enrollment count with link"""
        count = getattr(obj, 'enrollment_count', 0)
        if count > 0:
            url = reverse('admin:academic_courseenrollment_changelist')
            return format_html(
                '<a href="{}?course__id__exact={}">{}</a>',
                url, obj.pk, count
            )
        return count
    enrollment_count.short_description = 'Enrollments'
    
    def study_groups_count(self, obj):
        """Display study groups count with link"""
        count = getattr(obj, 'study_groups_count', 0)
        if count > 0:
            url = reverse('admin:academic_studygroup_changelist')
            return format_html(
                '<a href="{}?course__id__exact={}">{}</a>',
                url, obj.pk, count
            )
        return count
    study_groups_count.short_description = 'Study Groups'
    
    def activate_courses(self, request, queryset):
        """Bulk activate courses"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} courses were activated.')
    activate_courses.short_description = 'Activate selected courses'
    
    def deactivate_courses(self, request, queryset):
        """Bulk deactivate courses"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} courses were deactivated.')
    deactivate_courses.short_description = 'Deactivate selected courses'
    
    def open_enrollment(self, request, queryset):
        """Bulk open enrollment"""
        updated = queryset.update(enrollment_open=True)
        self.message_user(request, f'Enrollment opened for {updated} courses.')
    open_enrollment.short_description = 'Open enrollment for selected courses'
    
    def close_enrollment(self, request, queryset):
        """Bulk close enrollment"""
        updated = queryset.update(enrollment_open=False)
        self.message_user(request, f'Enrollment closed for {updated} courses.')
    close_enrollment.short_description = 'Close enrollment for selected courses'


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    """Admin interface for CourseEnrollment model"""
    list_display = (
        'user', 'course_code', 'course_name', 'role', 
        'enrollment_date', 'is_active', 'grade'
    )
    list_filter = (
        'role', 'is_active', 'enrollment_date', 
        'course__semester', 'course__year', 'course__institution'
    )
    search_fields = (
        'user__first_name', 'user__last_name', 'user__email',
        'course__course_code', 'course__course_name'
    )
    raw_id_fields = ('user', 'course')
    readonly_fields = ('enrollment_date',)
    ordering = ('-enrollment_date',)
    
    actions = ['activate_enrollments', 'deactivate_enrollments']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'course', 'course__institution'
        )
    
    def course_code(self, obj):
        """Display course code with link"""
        url = reverse('admin:academic_course_change', args=[obj.course.pk])
        return format_html('<a href="{}">{}</a>', url, obj.course.course_code)
    course_code.short_description = 'Course Code'
    course_code.admin_order_field = 'course__course_code'
    
    def course_name(self, obj):
        """Display course name"""
        return obj.course.course_name
    course_name.short_description = 'Course Name'
    course_name.admin_order_field = 'course__course_name'
    
    def activate_enrollments(self, request, queryset):
        """Bulk activate enrollments"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} enrollments were activated.')
    activate_enrollments.short_description = 'Activate selected enrollments'
    
    def deactivate_enrollments(self, request, queryset):
        """Bulk deactivate enrollments"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} enrollments were deactivated.')
    deactivate_enrollments.short_description = 'Deactivate selected enrollments'


class StudyGroupMemberInline(admin.TabularInline):
    """Inline admin for study group members"""
    model = StudyGroupMember
    extra = 0
    fields = ('user', 'role', 'joined_at', 'is_active', 'contributions')
    readonly_fields = ('joined_at',)
    raw_id_fields = ('user',)


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    """Admin interface for StudyGroup model"""
    list_display = (
        'name', 'course_info', 'creator', 'member_count', 
        'max_members', 'is_private', 'is_active', 'created_at'
    )
    list_filter = (
        'is_private', 'is_active', 'meeting_frequency', 
        'created_at', 'course__institution'
    )
    search_fields = (
        'name', 'description', 'creator__first_name', 
        'creator__last_name', 'course__course_code'
    )
    raw_id_fields = ('creator', 'course')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [StudyGroupMemberInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'course', 'creator')
        }),
        ('Settings', {
            'fields': ('max_members', 'is_private', 'is_active')
        }),
        ('Meeting Information', {
            'fields': ('meeting_location', 'meeting_time', 'meeting_frequency'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_groups', 'deactivate_groups', 'make_private', 'make_public']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'creator', 'course', 'course__institution'
        ).annotate(
            member_count=Count('members', filter=models.Q(members__is_active=True))
        )
    
    def course_info(self, obj):
        """Display course information"""
        if obj.course:
            url = reverse('admin:academic_course_change', args=[obj.course.pk])
            return format_html(
                '<a href="{}">{}</a>', url, obj.course.course_code
            )
        return mark_safe('<em>General</em>')
    course_info.short_description = 'Course'
    
    def member_count(self, obj):
        """Display member count with link"""
        count = getattr(obj, 'member_count', 0)
        if count > 0:
            url = reverse('admin:academic_studygroupmember_changelist')
            return format_html(
                '<a href="{}?group__id__exact={}">{}/{}</a>',
                url, obj.pk, count, obj.max_members
            )
        return f'0/{obj.max_members}'
    member_count.short_description = 'Members'
    
    def activate_groups(self, request, queryset):
        """Bulk activate study groups"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} study groups were activated.')
    activate_groups.short_description = 'Activate selected study groups'
    
    def deactivate_groups(self, request, queryset):
        """Bulk deactivate study groups"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} study groups were deactivated.')
    deactivate_groups.short_description = 'Deactivate selected study groups'
    
    def make_private(self, request, queryset):
        """Make study groups private"""
        updated = queryset.update(is_private=True)
        self.message_user(request, f'{updated} study groups were made private.')
    make_private.short_description = 'Make selected study groups private'
    
    def make_public(self, request, queryset):
        """Make study groups public"""
        updated = queryset.update(is_private=False)
        self.message_user(request, f'{updated} study groups were made public.')
    make_public.short_description = 'Make selected study groups public'


@admin.register(StudyGroupMember)
class StudyGroupMemberAdmin(admin.ModelAdmin):
    """Admin interface for StudyGroupMember model"""
    list_display = (
        'user', 'group_name', 'role', 'joined_at', 
        'is_active', 'contributions', 'last_active'
    )
    list_filter = (
        'role', 'is_active', 'joined_at', 
        'group__is_private', 'group__course__institution'
    )
    search_fields = (
        'user__first_name', 'user__last_name', 'user__email',
        'group__name', 'group__course__course_code'
    )
    raw_id_fields = ('user', 'group')
    readonly_fields = ('joined_at',)
    ordering = ('-joined_at',)
    
    actions = ['promote_to_moderator', 'demote_to_member', 'activate_memberships', 'deactivate_memberships']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'group', 'group__course'
        )
    
    def group_name(self, obj):
        """Display group name with link"""
        url = reverse('admin:academic_studygroup_change', args=[obj.group.pk])
        return format_html('<a href="{}">{}</a>', url, obj.group.name)
    group_name.short_description = 'Study Group'
    group_name.admin_order_field = 'group__name'
    
    def promote_to_moderator(self, request, queryset):
        """Promote members to moderator"""
        updated = queryset.update(role='moderator')
        self.message_user(request, f'{updated} members were promoted to moderator.')
    promote_to_moderator.short_description = 'Promote to moderator'
    
    def demote_to_member(self, request, queryset):
        """Demote moderators to member"""
        updated = queryset.update(role='member')
        self.message_user(request, f'{updated} moderators were demoted to member.')
    demote_to_member.short_description = 'Demote to member'
    
    def activate_memberships(self, request, queryset):
        """Bulk activate memberships"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} memberships were activated.')
    activate_memberships.short_description = 'Activate selected memberships'
    
    def deactivate_memberships(self, request, queryset):
        """Bulk deactivate memberships"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} memberships were deactivated.')
    deactivate_memberships.short_description = 'Deactivate selected memberships'


# Configure admin site headers
admin.site.site_header = 'Campus Connect Academic Administration'
admin.site.site_title = 'Academic Admin'
admin.site.index_title = 'Academic Management'
