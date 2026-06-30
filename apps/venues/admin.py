from django.contrib import admin
from .models import Venue, VenueImage, VenueAvailability, VenueBookingRequest


class VenueImageInline(admin.TabularInline):
    model = VenueImage
    extra = 1


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    """Admin for venues"""
    list_display = ('name', 'city', 'state', 'capacity', 'manager', 'is_active')
    list_filter = ('is_active', 'has_parking', 'has_wifi', 'has_catering', 'city', 'state')
    search_fields = ('name', 'city', 'manager__username')
    inlines = [VenueImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'manager')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Specifications', {
            'fields': ('capacity', 'area_sqft')
        }),
        ('Pricing', {
            'fields': ('hourly_rate', 'daily_rate')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_phone', 'contact_email')
        }),
        ('Features & Amenities', {
            'fields': ('has_parking', 'has_wifi', 'has_catering', 'has_av_equipment', 'has_accessibility')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(VenueAvailability)
class VenueAvailabilityAdmin(admin.ModelAdmin):
    """Admin for venue availability"""
    list_display = ('venue', 'date', 'start_time', 'end_time', 'is_available')
    list_filter = ('is_available', 'date')
    search_fields = ('venue__name',)
    date_hierarchy = 'date'


@admin.register(VenueBookingRequest)
class VenueBookingRequestAdmin(admin.ModelAdmin):
    """Admin for venue booking requests"""
    list_display = ('event_name', 'venue', 'requester', 'booking_date', 'status')
    list_filter = ('status', 'booking_date', 'created_at')
    search_fields = ('event_name', 'venue__name', 'requester__username')
    date_hierarchy = 'booking_date'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_name', 'event_description', 'requester')
        }),
        ('Booking Details', {
            'fields': ('venue', 'booking_date', 'start_time', 'end_time', 'expected_attendees')
        }),
        ('Status & Review', {
            'fields': ('status', 'reviewed_by', 'review_notes', 'reviewed_at')
        }),
        ('Pricing', {
            'fields': ('quoted_price',)
        }),
    )
