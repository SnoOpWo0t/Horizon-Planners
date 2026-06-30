from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with role-based permissions"""
    
    class Role(models.TextChoices):
        BASIC = 'basic', 'Basic User'
        HORIZON_PLANNER = 'horizon_planner', 'Horizon Planner'
        VENUE_MANAGER = 'venue_manager', 'Venue Manager'
        ADMIN = 'admin', 'Admin'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.BASIC,
        help_text='User role determines access permissions'
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_basic_user(self):
        return self.role == self.Role.BASIC
    
    @property
    def is_horizon_planner(self):
        return self.role == self.Role.HORIZON_PLANNER
    
    @property
    def is_venue_manager(self):
        return self.role == self.Role.VENUE_MANAGER
    
    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser


class RoleUpgradeRequest(models.Model):
    """Model for handling role upgrade requests"""
    
    class RequestedRole(models.TextChoices):
        HORIZON_PLANNER = 'horizon_planner', 'Horizon Planner'
        VENUE_MANAGER = 'venue_manager', 'Venue Manager'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upgrade_requests')
    requested_role = models.CharField(max_length=20, choices=RequestedRole.choices)
    reason = models.TextField(help_text='Reason for requesting role upgrade')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_requests'
    )
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'requested_role', 'status']
    
    def __str__(self):
        return f"{self.user.username} -> {self.get_requested_role_display()} ({self.get_status_display()})"
