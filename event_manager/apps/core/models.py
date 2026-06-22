from django.db import models
from django.conf import settings


class TimeStampedModel(models.Model):
    """Abstract base class for models that need created_at and updated_at fields"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Notification(TimeStampedModel):
    """Notification model for admin actions"""
    
    class NotificationType(models.TextChoices):
        EVENT_DEACTIVATED = 'event_deactivated', 'Event Deactivated'
        EVENT_DELETED = 'event_deleted', 'Event Deleted'
        VENUE_DEACTIVATED = 'venue_deactivated', 'Venue Deactivated'
        VENUE_DELETED = 'venue_deleted', 'Venue Deleted'
        OTHER = 'other', 'Other'
    
    class ActionReason(models.TextChoices):
        LATE_PAYMENT = 'late_payment', 'Late Payment'
        TECHNICAL_DIFFICULTIES = 'technical_difficulties', 'Technical Difficulties'
        POLICY_VIOLATION = 'policy_violation', 'Policy Violation'
        SECURITY_CONCERN = 'security_concern', 'Security Concern'
        FRAUD = 'fraud', 'Fraud'
        DUPLICATE = 'duplicate', 'Duplicate Account'
        MAINTENANCE = 'maintenance', 'Maintenance'
        OTHER = 'other', 'Other'
    
    # Recipients
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_notifications'
    )
    
    # Content
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.OTHER
    )
    reason = models.CharField(
        max_length=50,
        choices=ActionReason.choices,
        default=ActionReason.OTHER
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    # Related objects
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_notifications'
    )
    venue = models.ForeignKey(
        'venues.Venue',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_notifications'
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.recipient.username}"
    
    def mark_as_read(self):
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
