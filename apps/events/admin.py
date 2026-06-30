from django.contrib import admin
from .models import Category, Event, EventImage, Ticket, TicketPricing


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for event categories"""
    list_display = ('name', 'description', 'color')
    search_fields = ('name',)


class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin for events"""
    list_display = ('title', 'category', 'venue', 'manager', 'event_date', 'status', 'available_seats')
    list_filter = ('status', 'category', 'event_date', 'created_at')
    search_fields = ('title', 'description', 'manager__username')
    date_hierarchy = 'event_date'
    inlines = [EventImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'manager')
        }),
        ('Event Details', {
            'fields': ('venue', 'event_date', 'start_time', 'end_time')
        }),
        ('Ticketing', {
            'fields': ('total_seats', 'base_price')
        }),
        ('Status & Media', {
            'fields': ('status', 'is_featured', 'poster_image')
        }),
        ('Additional Information', {
            'fields': ('age_restriction', 'special_instructions'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Admin for tickets"""
    list_display = ('ticket_number', 'event', 'buyer', 'ticket_type', 'quantity', 'total_price', 'is_used')
    list_filter = ('ticket_type', 'is_used', 'created_at')
    search_fields = ('ticket_number', 'buyer__username', 'event__title')
    readonly_fields = ('ticket_number', 'qr_code', 'created_at')


@admin.register(TicketPricing)
class TicketPricingAdmin(admin.ModelAdmin):
    """Admin for ticket pricing"""
    list_display = ('event', 'name', 'ticket_type', 'price', 'available_quantity', 'is_active')
    list_filter = ('ticket_type', 'is_active')
    search_fields = ('event__title', 'name')
