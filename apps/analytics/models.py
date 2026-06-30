from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class EventAnalytics(TimeStampedModel):
    """Analytics data for events"""
    
    event = models.OneToOneField('events.Event', on_delete=models.CASCADE, related_name='analytics')
    
    # Ticket sales
    tickets_sold = models.PositiveIntegerField(default=0)
    gross_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Engagement metrics
    page_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    
    # Conversion metrics
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Social engagement
    likes = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    class Meta:
        verbose_name_plural = 'Event analytics'
    
    def __str__(self):
        return f"Analytics for {self.event.title}"


class VenueAnalytics(TimeStampedModel):
    """Analytics data for venues"""
    
    venue = models.OneToOneField('venues.Venue', on_delete=models.CASCADE, related_name='analytics')
    
    # Booking metrics
    total_bookings = models.PositiveIntegerField(default=0)
    confirmed_bookings = models.PositiveIntegerField(default=0)
    cancelled_bookings = models.PositiveIntegerField(default=0)
    
    # Revenue metrics
    gross_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_booking_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Utilization metrics
    occupancy_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    total_events_hosted = models.PositiveIntegerField(default=0)
    
    # Rating metrics
    reviews_count = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    class Meta:
        verbose_name_plural = 'Venue analytics'
    
    def __str__(self):
        return f"Analytics for {self.venue.name}"


class PlatformAnalytics(TimeStampedModel):
    """Overall platform analytics"""
    
    # Time period for this analytics record
    date = models.DateField(unique=True)
    
    # User metrics
    total_users = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    
    # Role distribution
    basic_users = models.PositiveIntegerField(default=0)
    horizon_planners = models.PositiveIntegerField(default=0)
    venue_managers = models.PositiveIntegerField(default=0)
    admins = models.PositiveIntegerField(default=0)
    
    # Event metrics
    total_events = models.PositiveIntegerField(default=0)
    active_events = models.PositiveIntegerField(default=0)
    completed_events = models.PositiveIntegerField(default=0)
    
    # Venue metrics
    total_venues = models.PositiveIntegerField(default=0)
    active_venues = models.PositiveIntegerField(default=0)
    
    # Financial metrics
    gross_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_transactions = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    total_reviews = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)
    platform_average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Platform analytics'
    
    def __str__(self):
        return f"Platform Analytics - {self.date}"


class UserActivity(TimeStampedModel):
    """Track user activities for analytics"""
    
    class ActivityType(models.TextChoices):
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        EVENT_VIEW = 'event_view', 'Event View'
        VENUE_VIEW = 'venue_view', 'Venue View'
        TICKET_PURCHASE = 'ticket_purchase', 'Ticket Purchase'
        REVIEW_SUBMIT = 'review_submit', 'Review Submit'
        COMMENT_POST = 'comment_post', 'Comment Post'
        EVENT_CREATE = 'event_create', 'Event Create'
        VENUE_CREATE = 'venue_create', 'Venue Create'
        ROLE_REQUEST = 'role_request', 'Role Upgrade Request'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ActivityType.choices)
    
    # Optional related objects
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, null=True, blank=True)
    venue = models.ForeignKey('venues.Venue', on_delete=models.CASCADE, null=True, blank=True)
    
    # Additional context data
    metadata = models.JSONField(default=dict, blank=True)
    
    # Session tracking
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} at {self.created_at}"
