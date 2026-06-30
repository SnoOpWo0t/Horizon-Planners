from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import User, RoleUpgradeRequest


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin for User model"""
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Profile', {
            'fields': ('role', 'phone_number', 'date_of_birth', 'profile_picture')
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role_badge', 'role', 'is_staff', 'date_joined')
    list_filter = UserAdmin.list_filter + ('role',)
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_editable = ('role',)  # Allow editing role directly in list view
    
    def role_badge(self, obj):
        """Display role with color coding"""
        colors = {
            'basic': 'secondary',
            'horizon_planner': 'primary', 
            'venue_manager': 'info',
            'admin': 'danger'
        }
        color = colors.get(obj.role, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = 'Role'


@admin.register(RoleUpgradeRequest)
class RoleUpgradeRequestAdmin(admin.ModelAdmin):
    """Admin for role upgrade requests"""
    list_display = ('user_info', 'requested_role_badge', 'status_badge', 'status', 'created_at', 'reviewed_by')
    list_filter = ('requested_role', 'status', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'reviewed_at')
    list_editable = ('status',)  # Allow editing status directly in list view
    actions = ['approve_requests', 'reject_requests']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'requested_role', 'reason', 'created_at')
        }),
        ('Review Information', {
            'fields': ('status', 'reviewed_by', 'review_notes', 'reviewed_at')
        }),
    )
    
    def user_info(self, obj):
        """Display user info with current role"""
        return format_html(
            '<strong>{}</strong><br><small>Current: {}</small>',
            obj.user.username,
            obj.user.get_role_display()
        )
    user_info.short_description = 'User'
    
    def requested_role_badge(self, obj):
        """Display requested role with badge"""
        return format_html(
            '<span class="badge badge-primary">{}</span>',
            obj.get_requested_role_display()
        )
    requested_role_badge.short_description = 'Requested Role'
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def approve_requests(self, request, queryset):
        """Bulk action to approve selected requests"""
        updated = 0
        for req in queryset.filter(status='pending'):
            # Update user role
            req.user.role = req.requested_role
            req.user.save()
            
            # Update request
            req.status = 'approved'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()
            updated += 1
            
        self.message_user(request, f'{updated} requests approved successfully.')
    approve_requests.short_description = 'Approve selected requests'
    
    def reject_requests(self, request, queryset):
        """Bulk action to reject selected requests"""
        updated = 0
        for req in queryset.filter(status='pending'):
            req.status = 'rejected'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()
            updated += 1
            
        self.message_user(request, f'{updated} requests rejected.')
    reject_requests.short_description = 'Reject selected requests'
