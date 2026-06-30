"""
Django signals for the Horizon Planner project
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.core.utils import generate_qr_code, send_notification_email

User = get_user_model()


@receiver(post_save, sender='events.Ticket')
def create_ticket_qr_code(sender, instance, created, **kwargs):
    """
    Generate QR code when a ticket is created
    """
    if created and not instance.qr_code:
        # Create QR code data with ticket info
        qr_data = f"TICKET:{instance.ticket_number}:EVENT:{instance.event.id}:USER:{instance.buyer.id}"
        instance.qr_code = qr_data
        instance.save(update_fields=['qr_code'])


@receiver(post_save, sender='payments.Payment')
def handle_payment_completion(sender, instance, **kwargs):
    """
    Handle actions when payment is completed
    """
    if instance.status == 'completed':
        # Send confirmation email
        send_notification_email(
            user=instance.user,
            subject=f"Payment Confirmed - {instance.event.title}",
            message=f"Your payment of ${instance.amount} for {instance.event.title} has been confirmed.",
            event=instance.event
        )


@receiver(post_save, sender='events.Event')
def create_event_analytics(sender, instance, created, **kwargs):
    """
    Create analytics record when an event is created
    """
    if created:
        from apps.analytics.models import EventAnalytics
        EventAnalytics.objects.get_or_create(event=instance)


@receiver(post_save, sender='venues.Venue')
def create_venue_analytics(sender, instance, created, **kwargs):
    """
    Create analytics record when a venue is created
    """
    if created:
        from apps.analytics.models import VenueAnalytics
        VenueAnalytics.objects.get_or_create(venue=instance)


@receiver(post_save, sender='users.RoleUpgradeRequest')
def notify_admin_role_request(sender, instance, created, **kwargs):
    """
    Notify admins when a new role upgrade request is created
    """
    if created:
        # Get all admin users
        admin_users = User.objects.filter(role='admin')
        for admin in admin_users:
            send_notification_email(
                user=admin,
                subject="New Role Upgrade Request",
                message=f"{instance.user.username} has requested an upgrade to {instance.get_requested_role_display()}."
            )


@receiver(post_save, sender='reviews.Review')
def update_rating_analytics(sender, instance, **kwargs):
    """
    Update average ratings when reviews are created/updated
    """
    if instance.status == 'approved':
        # Update event or venue analytics
        if instance.event:
            analytics = instance.event.analytics
            reviews = instance.event.reviews.filter(status='approved')
            analytics.reviews_count = reviews.count()
            if reviews.exists():
                analytics.average_rating = sum(r.rating for r in reviews) / reviews.count()
            analytics.save()
        
        elif instance.venue:
            analytics = instance.venue.analytics
            reviews = instance.venue.reviews.filter(status='approved')
            analytics.reviews_count = reviews.count()
            if reviews.exists():
                analytics.average_rating = sum(r.rating for r in reviews) / reviews.count()
            analytics.save()


@receiver(post_save, sender='venues.VenueBookingRequest')
def notify_venue_manager_booking_request(sender, instance, created, **kwargs):
    """
    Notify venue manager when a new booking request is made
    """
    if created:
        send_notification_email(
            user=instance.venue.manager,
            subject=f"New Booking Request - {instance.venue.name}",
            message=f"New booking request for {instance.event_name} on {instance.booking_date}."
        )
