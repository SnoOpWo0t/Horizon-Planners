from datetime import datetime

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.core.models import TimeStampedModel


class Category(models.Model):
    """Event categories"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code')
    icon = models.CharField(max_length=50, blank=True, help_text='Font Awesome icon class')
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return self.name


class Event(TimeStampedModel):
    """Main event model"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'
    
    # Basic information
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='events')
    
    # Horizon Planner
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='managed_events',
        limit_choices_to={'role': 'horizon_planner'}
    )
    
    # Venue and timing
    venue = models.ForeignKey('venues.Venue', on_delete=models.PROTECT, related_name='events')
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    # Legacy-compatible timing fields used by several templates/forms.
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    registration_deadline = models.DateTimeField(blank=True, null=True)
    
    # Ticketing
    total_seats = models.PositiveIntegerField(help_text='Total number of available seats')
    max_capacity = models.PositiveIntegerField(blank=True, null=True)
    min_capacity = models.PositiveIntegerField(blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    requires_approval = models.BooleanField(default=False)
    is_free = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_featured = models.BooleanField(default=False)
    
    # Media
    poster_image = models.ImageField(upload_to='events/posters/', blank=True, null=True)
    
    # Additional details
    age_restriction = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0), MaxValueValidator(21)]
    )
    special_instructions = models.TextField(blank=True)
    
    class Meta:
        ordering = ['event_date', 'start_time']
    
    def __str__(self):
        return f"{self.title} - {self.event_date}"

    def save(self, *args, **kwargs):
        # Keep legacy datetime fields and canonical date/time fields synchronized.
        if self.start_date:
            self.event_date = self.start_date.date()
            self.start_time = self.start_date.time().replace(second=0, microsecond=0)
        elif self.event_date and self.start_time:
            combined_start = datetime.combine(self.event_date, self.start_time)
            if timezone.is_naive(combined_start) and timezone.is_aware(timezone.now()):
                combined_start = timezone.make_aware(combined_start, timezone.get_current_timezone())
            self.start_date = combined_start

        if self.end_date:
            self.end_time = self.end_date.time().replace(second=0, microsecond=0)
        elif self.event_date and self.end_time:
            combined_end = datetime.combine(self.event_date, self.end_time)
            if timezone.is_naive(combined_end) and timezone.is_aware(timezone.now()):
                combined_end = timezone.make_aware(combined_end, timezone.get_current_timezone())
            self.end_date = combined_end

        if self.max_capacity and not self.total_seats:
            self.total_seats = self.max_capacity
        elif self.total_seats and not self.max_capacity:
            self.max_capacity = self.total_seats
        elif self.total_seats and self.max_capacity and self.total_seats != self.max_capacity:
            self.total_seats = self.max_capacity

        if self.is_free:
            self.base_price = 0

        super().save(*args, **kwargs)
    
    @property
    def available_seats(self):
        booked_seats = self.orders.filter(
            payment__status='completed'
        ).aggregate(total=models.Sum('ticket_quantity'))['total'] or 0
        return self.total_seats - booked_seats
    
    @property
    def is_sold_out(self):
        return self.available_seats <= 0

    @property
    def remaining_tickets(self):
        return self.available_seats

    @property
    def tickets_sold(self):
        return max(0, self.total_seats - self.available_seats)

    @property
    def capacity_percentage(self):
        if not self.total_seats:
            return 0
        return round((self.tickets_sold / self.total_seats) * 100)

    @property
    def image(self):
        return self.poster_image

    @property
    def is_upcoming(self):
        if self.start_date:
            return self.start_date > timezone.now()
        return False

    @property
    def is_ongoing(self):
        if self.start_date and self.end_date:
            now = timezone.now()
            return self.start_date <= now <= self.end_date
        return False

    @property
    def is_past(self):
        if self.end_date:
            return self.end_date < timezone.now()
        return self.event_date < timezone.localdate()
    
    @property
    def attendance_percentage(self):
        if self.total_seats == 0:
            return 0
        return ((self.total_seats - self.available_seats) / self.total_seats) * 100


class EventImage(models.Model):
    """Additional images for events"""
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='events/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.event.title} - {self.caption or 'Image'}"


class Ticket(TimeStampedModel):
    """Individual ticket model"""
    
    class TicketType(models.TextChoices):
        REGULAR = 'regular', 'Regular'
        VIP = 'vip', 'VIP'
        STUDENT = 'student', 'Student'
        SENIOR = 'senior', 'Senior'
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    
    # Ticket details
    ticket_type = models.CharField(max_length=20, choices=TicketType.choices, default=TicketType.REGULAR)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Ticket identification
    ticket_number = models.CharField(max_length=20, unique=True)
    qr_code = models.TextField(blank=True)  # Store QR code data
    
    # Status
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.event.title}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            import uuid
            self.ticket_number = str(uuid.uuid4())[:12].upper()
        
        if not self.total_price:
            self.total_price = self.unit_price * self.quantity
            
        super().save(*args, **kwargs)


class TicketPricing(models.Model):
    """Dynamic pricing for different ticket types"""
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='pricing_tiers')
    ticket_type = models.CharField(max_length=20, choices=Ticket.TicketType.choices)
    name = models.CharField(max_length=100)  # e.g., "Early Bird", "Regular", "Last Minute"
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available_quantity = models.PositiveIntegerField()
    
    # Time-based pricing
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['price']
        unique_together = ['event', 'ticket_type', 'name']
    
    def __str__(self):
        return f"{self.event.title} - {self.name} ({self.get_ticket_type_display()}): ${self.price}"
