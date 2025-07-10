from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    DirectMessage, 
    GroupChat, 
    GroupChatMember, 
    GroupMessage, 
    Notification,
    MessageAttachment
)


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'content_preview', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at', 'updated_at']
    search_fields = ['sender__username', 'recipient__username', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['sender', 'recipient']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sender', 'recipient')
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        count = 0
        for message in queryset:
            if not message.is_read:
                message.mark_as_read()
                count += 1
        self.message_user(request, f'Marked {count} messages as read.')
    mark_as_read.short_description = 'Mark selected messages as read'
    
    def mark_as_unread(self, request, queryset):
        count = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(request, f'Marked {count} messages as unread.')
    mark_as_unread.short_description = 'Mark selected messages as unread'


class GroupChatMemberInline(admin.TabularInline):
    model = GroupChatMember
    extra = 0
    readonly_fields = ['joined_at', 'left_at']
    raw_id_fields = ['user']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(GroupChat)
class GroupChatAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'member_count_display', 'is_private', 'is_active', 'created_at']
    list_filter = ['is_private', 'is_active', 'created_at', 'updated_at']
    search_fields = ['name', 'description', 'creator__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'member_count_display']
    raw_id_fields = ['creator']
    date_hierarchy = 'created_at'
    inlines = [GroupChatMemberInline]
    
    def member_count_display(self, obj):
        return obj.get_member_count()
    member_count_display.short_description = 'Active Members'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('creator')
    
    actions = ['activate_chats', 'deactivate_chats']
    
    def activate_chats(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'Activated {count} group chats.')
    activate_chats.short_description = 'Activate selected group chats'
    
    def deactivate_chats(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {count} group chats.')
    deactivate_chats.short_description = 'Deactivate selected group chats'


@admin.register(GroupChatMember)
class GroupChatMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'chat', 'is_admin', 'is_active', 'joined_at']
    list_filter = ['is_admin', 'is_active', 'joined_at', 'left_at']
    search_fields = ['user__username', 'chat__name']
    readonly_fields = ['joined_at', 'left_at']
    raw_id_fields = ['user', 'chat']
    date_hierarchy = 'joined_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'chat')
    
    actions = ['make_admin', 'remove_admin', 'activate_members', 'deactivate_members']
    
    def make_admin(self, request, queryset):
        count = queryset.update(is_admin=True)
        self.message_user(request, f'Made {count} members admin.')
    make_admin.short_description = 'Make selected members admin'
    
    def remove_admin(self, request, queryset):
        count = queryset.update(is_admin=False)
        self.message_user(request, f'Removed admin from {count} members.')
    remove_admin.short_description = 'Remove admin from selected members'
    
    def activate_members(self, request, queryset):
        count = queryset.update(is_active=True, left_at=None)
        self.message_user(request, f'Activated {count} members.')
    activate_members.short_description = 'Activate selected members'
    
    def deactivate_members(self, request, queryset):
        count = queryset.update(is_active=False, left_at=timezone.now())
        self.message_user(request, f'Deactivated {count} members.')
    deactivate_members.short_description = 'Deactivate selected members'


@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'chat', 'content_preview', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['sender__username', 'chat__name', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['sender', 'chat']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sender', 'chat')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'actor', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'content', 'actor__username']
    readonly_fields = ['id', 'created_at', 'target_object_link']
    raw_id_fields = ['user', 'actor']
    date_hierarchy = 'created_at'
    
    def target_object_link(self, obj):
        if obj.target_object:
            url = obj.get_target_url()
            if url:
                return format_html('<a href="{}" target="_blank">View Target</a>', url)
        return 'No target'
    target_object_link.short_description = 'Target Object'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'actor')
    
    actions = ['mark_as_read', 'mark_as_unread', 'delete_old_notifications']
    
    def mark_as_read(self, request, queryset):
        count = 0
        for notification in queryset:
            if not notification.is_read:
                notification.mark_as_read()
                count += 1
        self.message_user(request, f'Marked {count} notifications as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def mark_as_unread(self, request, queryset):
        count = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(request, f'Marked {count} notifications as unread.')
    mark_as_unread.short_description = 'Mark selected notifications as unread'
    
    def delete_old_notifications(self, request, queryset):
        # Delete notifications older than 30 days that are read
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        count = queryset.filter(
            is_read=True,
            read_at__lt=cutoff_date
        ).delete()[0]
        self.message_user(request, f'Deleted {count} old notifications.')
    delete_old_notifications.short_description = 'Delete old read notifications'


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'file_type', 'uploaded_by', 'file_size_display', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['filename', 'uploaded_by__username']
    readonly_fields = ['id', 'created_at', 'file_size_display']
    raw_id_fields = ['uploaded_by']
    date_hierarchy = 'created_at'
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = 'File Size'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('uploaded_by')
    
    actions = ['delete_large_files']
    
    def delete_large_files(self, request, queryset):
        # Delete files larger than 10MB
        large_files = queryset.filter(file_size__gt=10*1024*1024)
        count = large_files.count()
        large_files.delete()
        self.message_user(request, f'Deleted {count} large files.')
    delete_large_files.short_description = 'Delete files larger than 10MB'


# Custom admin site configuration
admin.site.site_header = 'CampHub Messaging Administration'
admin.site.site_title = 'CampHub Messaging Admin'
admin.site.index_title = 'Welcome to CampHub Messaging Administration'
