from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum
from .models import Event, Category, Ticket
from .forms import EventForm, BookTicketForm


class EventListView(ListView):
    """Home page - list all published events"""
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Event.objects.filter(status='published').select_related('venue', 'category')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        # Category filter
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Venue filter
        venue_id = self.request.GET.get('venue')
        if venue_id:
            queryset = queryset.filter(venue_id=venue_id)
        
        return queryset.order_by('event_date', 'start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        return context


class EventDetailView(DetailView):
    """Detailed view of an event"""
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    
    def get_queryset(self):
        return Event.objects.filter(status='published').select_related('venue', 'category', 'manager')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        
        # Get approved reviews and comments
        context['reviews'] = event.reviews.filter(status='approved').order_by('-created_at')[:5]
        context['comments'] = event.comments.filter(status='approved').order_by('-created_at')[:10]
        
        # Check if user can book tickets
        if self.request.user.is_authenticated:
            context['user_has_ticket'] = event.tickets.filter(
                buyer=self.request.user,
                payment__status='completed'
            ).exists()
        
        return context


class HorizonPlannerRequiredMixin(UserPassesTestMixin):
    """Mixin to require Horizon Planner role"""
    def test_func(self):
        return (self.request.user.is_authenticated and 
                (self.request.user.is_horizon_planner or self.request.user.is_admin_user))


class HorizonPlannerDashboardView(HorizonPlannerRequiredMixin, ListView):
    """Dashboard for Horizon Planners"""
    model = Event
    template_name = 'events/manager_dashboard.html'
    context_object_name = 'events'
    
    def get_queryset(self):
        if self.request.user.is_admin_user:
            return Event.objects.all().select_related('venue', 'category')
        return Event.objects.filter(manager=self.request.user).select_related('venue', 'category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        context['total_events'] = queryset.count()
        context['published_events'] = queryset.filter(status='published').count()
        context['draft_events'] = queryset.filter(status='draft').count()
        context['completed_events'] = queryset.filter(status='completed').count()
        
        return context


class CreateEventView(HorizonPlannerRequiredMixin, CreateView):
    """Create new event"""
    model = Event
    form_class = EventForm
    template_name = 'events/create_event.html'
    success_url = reverse_lazy('events:manager_dashboard')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        
        # Add available venues for the dropdown
        from apps.venues.models import Venue
        context['available_venues'] = Venue.objects.filter(is_active=True).order_by('name')
        
        return context
    
    def form_valid(self, form):
        form.instance.manager = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Event created successfully!')
        return response


class EditEventView(HorizonPlannerRequiredMixin, UpdateView):
    """Edit existing event"""
    model = Event
    form_class = EventForm
    template_name = 'events/edit_event.html'
    
    def get_queryset(self):
        if self.request.user.is_admin_user:
            return Event.objects.all()
        return Event.objects.filter(manager=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('events:manage_event', kwargs={'pk': self.object.pk})


class ManageEventView(HorizonPlannerRequiredMixin, DetailView):
    """Manage specific event"""
    model = Event
    template_name = 'events/manage_event.html'
    context_object_name = 'event'
    
    def get_queryset(self):
        if self.request.user.is_admin_user:
            return Event.objects.all()
        return Event.objects.filter(manager=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        
        # Get ticket sales data
        tickets = event.tickets.filter(payment__status='completed')
        context['tickets_sold'] = tickets.aggregate(total=Sum('quantity'))['total'] or 0
        context['revenue'] = tickets.aggregate(total=Sum('total_price'))['total'] or 0
        context['recent_sales'] = tickets.order_by('-created_at')[:10]
        
        return context


class DeleteEventView(HorizonPlannerRequiredMixin, DeleteView):
    """Delete event"""
    model = Event
    template_name = 'events/delete_event.html'
    success_url = reverse_lazy('events:manager_dashboard')
    
    def get_queryset(self):
        if self.request.user.is_admin_user:
            return Event.objects.all()
        return Event.objects.filter(manager=self.request.user)


class BookTicketView(LoginRequiredMixin, CreateView):
    """Book tickets for an event"""
    model = Ticket
    form_class = BookTicketForm
    template_name = 'events/book_ticket.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_id = self.kwargs.get('pk')
        context['event'] = get_object_or_404(Event, pk=event_id, status='published')
        return context
    
    def form_valid(self, form):
        event_id = self.kwargs.get('pk')
        event = get_object_or_404(Event, pk=event_id, status='published')
        
        # Check if tickets are available
        if event.available_seats < form.cleaned_data['quantity']:
            messages.error(self.request, 'Not enough tickets available.')
            return self.form_invalid(form)
        
        form.instance.event = event
        form.instance.buyer = self.request.user
        form.instance.unit_price = event.base_price
        
        response = super().form_valid(form)
        
        # Redirect to payment processing
        return redirect('payments:process_payment', event_id=event.id)


class CategoryEventListView(ListView):
    """List events by category"""
    model = Event
    template_name = 'events/category_events.html'
    context_object_name = 'events'
    paginate_by = 12
    
    def get_queryset(self):
        category_id = self.kwargs.get('pk')
        return Event.objects.filter(
            category_id=category_id,
            status='published'
        ).select_related('venue', 'category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_id = self.kwargs.get('pk')
        context['category'] = get_object_or_404(Category, pk=category_id)
        return context


class EventAnalyticsView(HorizonPlannerRequiredMixin, View):
    """Event analytics overview"""
    template_name = 'events/analytics.html'
    
    def get(self, request):
        if request.user.is_admin_user:
            events = Event.objects.all()
        else:
            events = Event.objects.filter(manager=request.user)
        
        # Get recent events with related data
        recent_events = events.select_related('category', 'manager').prefetch_related('tickets')[:10]
        
        # Calculate total attendees
        total_attendees = 0
        for event in events:
            total_attendees += event.tickets.aggregate(
                total=Sum('quantity')
            )['total'] or 0
        
        context = {
            'total_events': events.count(),
            'total_attendees': total_attendees,
            'total_revenue': events.aggregate(
                total=Sum('tickets__total_price')
            )['total'] or 0,
            'total_tickets_sold': events.aggregate(
                total=Sum('tickets__quantity')
            )['total'] or 0,
            'recent_events': recent_events,
        }
        
        return render(request, self.template_name, context)


class EventDetailAnalyticsView(HorizonPlannerRequiredMixin, DetailView):
    """Detailed analytics for a specific event"""
    model = Event
    template_name = 'events/event_detail_analytics.html'
    context_object_name = 'event'
    
    def get_queryset(self):
        if self.request.user.is_admin_user:
            return Event.objects.all()
        return Event.objects.filter(manager=self.request.user)


# Category Management Views
class CategoryListView(HorizonPlannerRequiredMixin, ListView):
    """List all categories"""
    model = Category
    template_name = 'events/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20


class CreateCategoryView(HorizonPlannerRequiredMixin, CreateView):
    """Create new category"""
    model = Category
    template_name = 'events/create_category.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('events:category_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Category "{form.instance.name}" created successfully!')
        return response


class EditCategoryView(HorizonPlannerRequiredMixin, UpdateView):
    """Edit existing category"""
    model = Category
    template_name = 'events/edit_category.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('events:category_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Category "{form.instance.name}" updated successfully!')
        return response


class DeleteCategoryView(HorizonPlannerRequiredMixin, DeleteView):
    """Delete category"""
    model = Category
    template_name = 'events/delete_category.html'
    success_url = reverse_lazy('events:category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['events_count'] = self.get_object().events.count()
        return context
    
    def get_queryset(self):
        if self.request.user.is_admin_user:
            return Event.objects.all()
        return Event.objects.filter(manager=self.request.user)
