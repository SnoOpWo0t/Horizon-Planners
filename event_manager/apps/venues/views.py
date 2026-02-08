from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, TemplateView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from .models import Venue, VenueImage, VenueBookingRequest
from apps.events.models import Event


class VenueListView(ListView):
    """List all venues"""
    model = Venue
    template_name = 'venues/venue_list.html'
    context_object_name = 'venues'
    paginate_by = 12
    
    def get_queryset(self):
        # Show all venues if user is admin, only active ones otherwise
        if self.request.user.is_authenticated and self.request.user.is_admin_user:
            queryset = Venue.objects.all()
        else:
            queryset = Venue.objects.filter(is_active=True)
        
        # Add related data to reduce queries
        queryset = queryset.select_related('manager').prefetch_related('events', 'booking_requests')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(address__icontains=search) |
                Q(city__icontains=search)
            )
        
        # Capacity filter
        min_capacity = self.request.GET.get('min_capacity')
        if min_capacity:
            queryset = queryset.filter(capacity__gte=min_capacity)
            
        # City filter
        city = self.request.GET.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
            
        # Sort by
        sort_by = self.request.GET.get('sort', 'name')
        if sort_by == 'capacity':
            queryset = queryset.order_by('-capacity')
        elif sort_by == 'price':
            queryset = queryset.order_by('hourly_rate')
        elif sort_by == 'rating':
            queryset = queryset.order_by('-average_rating')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('name')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get unique cities for filter dropdown
        context['cities'] = Venue.objects.values_list('city', flat=True).distinct().order_by('city')
        
        # Get current filter values
        context['current_search'] = self.request.GET.get('search', '')
        context['current_min_capacity'] = self.request.GET.get('min_capacity', '')
        context['current_city'] = self.request.GET.get('city', '')
        context['current_sort'] = self.request.GET.get('sort', 'name')
        
        return context


class VenueManagerRequiredMixin(UserPassesTestMixin):
    """Mixin to require venue manager role"""
    def test_func(self):
        return (self.request.user.is_authenticated and 
                (self.request.user.is_venue_manager or self.request.user.is_admin_user))


class VenueManagerDashboardView(VenueManagerRequiredMixin, TemplateView):
    """Dashboard for venue managers"""
    template_name = 'venues/manager_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_venues = Venue.objects.filter(manager=self.request.user)
        
        context.update({
            'venues': user_venues,
            'total_venues': user_venues.count(),
            'total_bookings': VenueBookingRequest.objects.filter(venue__manager=self.request.user).count(),
            'pending_requests': VenueBookingRequest.objects.filter(
                venue__manager=self.request.user, 
                status='pending'
            ).count(),
            'monthly_revenue': 0,  # Calculate based on bookings
            'recent_requests': VenueBookingRequest.objects.filter(
                venue__manager=self.request.user
            ).order_by('-created_at')[:5],
        })
        return context


# Venue Detail View
class VenueDetailView(DetailView):
    model = Venue
    template_name = 'venues/venue_detail.html'
    context_object_name = 'venue'
    slug_field = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venue = self.get_object()
        
        # Get upcoming events for this venue (next 4 events)
        from django.utils import timezone
        from apps.events.models import Event
        try:
            upcoming_events = Event.objects.filter(
                venue=venue,
                event_date__gte=timezone.now().date(),
                status='published'
            ).select_related('category', 'manager').order_by('event_date', 'start_time')[:4]
        except Exception:
            upcoming_events = []
        
        # Get venue images (primary first, then others)
        try:
            venue_images = venue.images.all().order_by('-is_primary', 'id')
        except Exception:
            venue_images = []
        
        # Get recent reviews (latest 3 approved reviews)
        try:
            recent_reviews = venue.reviews.filter(
                status='approved'
            ).select_related('user').order_by('-created_at')[:3]
        except Exception:
            recent_reviews = []
        
        # Calculate venue statistics
        try:
            total_events = venue.events.count()
        except Exception:
            total_events = 0
        
        try:
            total_reviews = venue.reviews.count()
        except Exception:
            total_reviews = 0
        
        # Check if current user has booked this venue
        user_has_booked = False
        if self.request.user.is_authenticated:
            try:
                user_has_booked = venue.bookings.filter(
                    user=self.request.user,
                    status__in=['confirmed', 'completed']
                ).exists()
            except Exception:
                user_has_booked = False
        
        context.update({
            'upcoming_events': upcoming_events,
            'venue_images': venue_images,
            'recent_reviews': recent_reviews,
            'total_events': total_events,
            'total_reviews': total_reviews,
            'user_has_booked': user_has_booked,
        })
        
        return context


class CreateVenueView(VenueManagerRequiredMixin, CreateView):
    model = Venue
    template_name = 'venues/create_venue.html'
    fields = [
        'name', 'description', 'address', 'city', 'state', 'postal_code', 
        'country', 'capacity', 'area_sqft', 'hourly_rate', 'daily_rate',
        'contact_person', 'contact_phone', 'contact_email',
        'has_parking', 'has_wifi', 'has_catering', 'has_av_equipment', 'has_accessibility',
        'is_active'
    ]
    
    def get_success_url(self):
        return reverse('venues:manage_venue', kwargs={'slug': self.object.slug})
    
    def form_valid(self, form):
        form.instance.manager = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Venue "{form.instance.name}" created successfully!')
        return response


class ManageVenueView(VenueManagerRequiredMixin, DetailView):
    model = Venue
    template_name = 'venues/manage_venue.html'
    context_object_name = 'venue'
    slug_field = 'slug'
    
    def get_queryset(self):
        return Venue.objects.filter(manager=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venue = self.get_object()
        
        # Get pending booking requests
        pending_bookings = VenueBookingRequest.objects.filter(
            venue=venue,
            status='pending'
        ).order_by('-created_at')
        
        context.update({
            'pending_bookings': pending_bookings[:3],  # Show only first 3
            'pending_bookings_count': pending_bookings.count(),
            'total_revenue': 0,  # This would be calculated from actual bookings
        })
        
        return context


class EditVenueView(VenueManagerRequiredMixin, UpdateView):
    model = Venue
    template_name = 'venues/edit_venue.html'
    fields = [
        'name', 'description', 'address', 'city', 'state', 'postal_code', 
        'country', 'capacity', 'area_sqft', 'hourly_rate', 'daily_rate',
        'contact_person', 'contact_phone', 'contact_email',
        'has_parking', 'has_wifi', 'has_catering', 'has_av_equipment', 'has_accessibility',
        'is_active'
    ]
    slug_field = 'slug'
    
    def get_queryset(self):
        if self.request.user.is_admin_user:
            return Venue.objects.all()
        return Venue.objects.filter(manager=self.request.user)
    
    def get_success_url(self):
        return reverse('venues:manage_venue', kwargs={'slug': self.object.slug})
    
    def form_valid(self, form):
        messages.success(self.request, f'Venue "{form.instance.name}" has been updated successfully!')
        return super().form_valid(form)


class DeleteVenueView(VenueManagerRequiredMixin, DeleteView):
    model = Venue
    template_name = 'venues/delete_venue.html'
    context_object_name = 'venue'
    slug_field = 'slug'
    success_url = reverse_lazy('venues:venue_list')
    
    def get_queryset(self):
        if self.request.user.is_admin_user:
            return Venue.objects.all()
        return Venue.objects.filter(manager=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        venue = self.get_object()
        messages.success(request, f'Venue "{venue.name}" has been deleted successfully.')
        return super().delete(request, *args, **kwargs)

class VenueBookingsView(VenueManagerRequiredMixin, TemplateView):
    template_name = 'venues/venue_bookings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['booking_requests'] = VenueBookingRequest.objects.filter(
            venue__manager=self.request.user
        ).order_by('-created_at')
        return context

class ApproveBookingRequestView(VenueManagerRequiredMixin, View):
    def post(self, request, pk):
        """Approve a venue booking request"""
        booking_request = get_object_or_404(
            VenueBookingRequest, 
            pk=pk, 
            venue__manager=request.user
        )
        
        try:
            booking_request.status = 'approved'
            booking_request.reviewed_at = timezone.now()
            booking_request.reviewed_by = request.user
            booking_request.review_notes = request.POST.get('notes', '')
            booking_request.save()
            
            messages.success(
                request, 
                f'Booking request for "{booking_request.event_name}" has been approved.'
            )
            
            return redirect('venues:venue_bookings')
            
        except Exception as e:
            messages.error(request, f'Error approving booking request: {str(e)}')
            return redirect('venues:venue_bookings')

class RejectBookingRequestView(VenueManagerRequiredMixin, View):
    def post(self, request, pk):
        """Reject a venue booking request"""
        booking_request = get_object_or_404(
            VenueBookingRequest, 
            pk=pk, 
            venue__manager=request.user
        )
        
        try:
            booking_request.status = 'rejected'
            booking_request.reviewed_at = timezone.now()
            booking_request.reviewed_by = request.user
            booking_request.review_notes = request.POST.get('notes', '')
            booking_request.save()
            
            messages.info(
                request, 
                f'Booking request for "{booking_request.event_name}" has been rejected.'
            )
            
            return redirect('venues:venue_bookings')
            
        except Exception as e:
            messages.error(request, f'Error rejecting booking request: {str(e)}')
            return redirect('venues:venue_bookings')

class ManageVenueAvailabilityView(VenueManagerRequiredMixin, TemplateView):
    template_name = 'venues/manage_availability.html'

class VenueAnalyticsView(VenueManagerRequiredMixin, TemplateView):
    template_name = 'venues/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get venues for the current user
        user_venues = Venue.objects.filter(manager=self.request.user)
        
        # Calculate analytics data
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Sum, Count, Avg
        
        # Date range for analytics (last 30 days by default)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Sample data - in real implementation, this would come from booking models
        total_bookings = 0
        total_revenue = 0
        total_guests = 0
        
        # Try to get real data from events if available
        try:
            from apps.events.models import Event
            venue_events = Event.objects.filter(
                venue__in=user_venues,
                event_date__range=[start_date, end_date]
            )
            total_bookings = venue_events.count()
            # Estimate revenue based on events (this would be from actual booking records)
            total_revenue = total_bookings * 1500  # Average revenue per event
        except:
            # Fallback to sample data
            total_bookings = 24
            total_revenue = 36000
        
        total_guests = total_bookings * 150  # Average guests per event
        
        # Calculate average rating
        try:
            average_rating = user_venues.aggregate(
                avg_rating=Avg('reviews__rating')
            )['avg_rating'] or 4.2
        except:
            average_rating = 4.2
        
        # Sample recent bookings data
        recent_bookings = [
            {
                'event_title': 'Corporate Annual Meeting',
                'organizer_name': 'Tech Solutions Inc',
                'event_date': timezone.now().date() - timedelta(days=2),
                'duration': 8,
                'guest_count': 200,
                'revenue': 2400,
                'status': 'success',
                'status_display': 'Completed'
            },
            {
                'event_title': 'Wedding Reception',
                'organizer_name': 'Sarah & Mike Johnson',
                'event_date': timezone.now().date() - timedelta(days=5),
                'duration': 6,
                'guest_count': 150,
                'revenue': 1800,
                'status': 'success',
                'status_display': 'Completed'
            },
            {
                'event_title': 'Product Launch Event',
                'organizer_name': 'Marketing Pro Ltd',
                'event_date': timezone.now().date() + timedelta(days=10),
                'duration': 4,
                'guest_count': 100,
                'revenue': 1200,
                'status': 'warning',
                'status_display': 'Confirmed'
            },
        ]
        
        context.update({
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
            'total_guests': total_guests,
            'average_rating': round(average_rating, 1),
            'recent_bookings': recent_bookings,
            'utilization_percentage': 78,
            'weekday_utilization': 65,
            'weekend_utilization': 88,
            'monthly_progress': 82,
            'quarterly_progress': 70,
            'venue_rental': total_revenue * 0.7,
            'catering_revenue': total_revenue * 0.2,
            'av_equipment': total_revenue * 0.05,
            'extras': total_revenue * 0.05,
            'projected_monthly': total_revenue * 1.3,
            'user_venues': user_venues,
        })
        
        return context

class BookVenueView(LoginRequiredMixin, DetailView):
    model = Venue
    template_name = 'venues/book_venue.html'
    context_object_name = 'venue'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        context['today'] = timezone.now().date()
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle venue booking request submission"""
        venue = self.get_object()
        
        try:
            # Create booking request
            booking_request = VenueBookingRequest.objects.create(
                venue=venue,
                requester=request.user,
                event_name=request.POST.get('event_title'),
                event_description=request.POST.get('event_description', ''),
                booking_date=request.POST.get('start_date'),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time'),
                expected_attendees=request.POST.get('expected_guests'),
                status='pending'
            )
            
            messages.success(
                request, 
                f'Your booking request for "{venue.name}" has been submitted successfully! '
                f'The venue manager will review and respond to your request.'
            )
            
            return redirect('venues:venue_detail', slug=venue.slug)
            
        except Exception as e:
            messages.error(
                request, 
                f'There was an error submitting your booking request: {str(e)}'
            )
            return self.get(request, *args, **kwargs)
