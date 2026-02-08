from django.db import models
from django.conf import settings
from django.utils.text import slugify
from apps.core.models import TimeStampedModel


class Venue(TimeStampedModel):
    """Model for venue listings"""
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    
    # Venue specifications
    capacity = models.PositiveIntegerField(help_text='Maximum number of people')
    area_sqft = models.PositiveIntegerField(null=True, blank=True, help_text='Area in square feet')
    
    # Pricing
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Contact information
    contact_person = models.CharField(max_length=200)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    
    # Features and amenities
    has_parking = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=False)
    has_catering = models.BooleanField(default=False)
    has_av_equipment = models.BooleanField(default=False)
    has_accessibility = models.BooleanField(default=False)
    
    # Management
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='managed_venues',
        limit_choices_to={'role': 'venue_manager'}
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.city}")
            # Ensure slug is unique
            original_slug = self.slug
            counter = 1
            while Venue.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"
    
    @property
    def average_rating(self):
        try:
            reviews = self.reviews.filter(status='approved')
            if reviews.exists():
                return sum(review.rating for review in reviews) / reviews.count()
            return 0
        except Exception:
            return 0


class VenueImage(models.Model):
    """Model for venue images"""
    
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='venues/images/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', '-uploaded_at']
    
    def __str__(self):
        return f"{self.venue.name} - {self.caption or 'Image'}"


class VenueAvailability(models.Model):
    """Model for venue availability scheduling"""
    
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='availability_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['venue', 'date', 'start_time']
    
    def __str__(self):
        return f"{self.venue.name} - {self.date} {self.start_time}-{self.end_time}"


class VenueBookingRequest(TimeStampedModel):
    """Model for venue booking requests from Horizon Planners"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'
    
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='booking_requests')
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='venue_booking_requests'
    )
    
    # Event details
    event_name = models.CharField(max_length=200)
    event_description = models.TextField()
    
    # Booking details
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    expected_attendees = models.PositiveIntegerField()
    
    # Status and approval
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_venue_bookings'
    )
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Pricing
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event_name} at {self.venue.name} - {self.get_status_display()}"
