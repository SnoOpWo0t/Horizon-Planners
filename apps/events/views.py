from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from apps.core.pagination import CONTENT_CARDS_PER_PAGE, build_query_string, paginate_queryset
from .models import Event, Category, Ticket
from .forms import EventForm, BookTicketForm
from apps.venues.models import Venue


class EventListView(ListView):
    """Home page - list all published events"""
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = CONTENT_CARDS_PER_PAGE
    
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
        
        # Order by featured first, then by event date
        return queryset.order_by('-is_featured', 'event_date', 'start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['venues'] = Venue.objects.filter(is_active=True).order_by('name')
        context['search_query'] = self.request.GET.get('search', '')
        context['pagination_query'] = build_query_string(self.request, ['page'])
        # Get featured events separately for potential featured section
        context['featured_events'] = Event.objects.filter(
            status='published', 
            is_featured=True
        ).select_related('venue', 'category')[:5]
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
        
        # Reviews
        approved_reviews = event.reviews.filter(status='approved')
        context['reviews'] = approved_reviews.order_by('-created_at')[:5]
        context['reviews_count'] = approved_reviews.count()
        context['avg_rating'] = approved_reviews.aggregate(Avg('rating'))['rating__avg']
        
        # Threaded Comments (Top-level only, prefetched replies)
        approved_comments = event.comments.filter(status='approved', parent__isnull=True)
        context['comments'] = approved_comments.select_related('user').prefetch_related('replies__user').order_by('-is_pinned', '-created_at')[:10]
        context['comments_count'] = event.comments.filter(status='approved').count()
        
        # User specific logic
        if self.request.user.is_authenticated:
            # Check if user can book tickets or has a ticket
            context['user_has_ticket'] = event.orders.filter(
                user=self.request.user,
                payment__status='completed'
            ).exists()
            
            # Check if user can write a review (completed order)
            context['has_completed_order'] = context['user_has_ticket']
            
            # Check if user already reviewed
            context['already_reviewed'] = event.reviews.filter(
                user=self.request.user
            ).exists()
            
            # Get comment likes for current user
            from apps.reviews.models import CommentLike
            context['user_liked_ids'] = set(
                CommentLike.objects.filter(
                    user=self.request.user,
                    comment__event=event
                ).values_list('comment_id', flat=True)
            )
        
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
        
        from apps.payments.models import Order
        
        context['total_events'] = queryset.count()
        context['published_events'] = queryset.filter(status='published').count()
        context['draft_events'] = queryset.filter(status='draft').count()
        context['completed_events'] = queryset.filter(status='completed').count()
        
        # Orders stats
        if self.request.user.is_admin_user:
            context['pending_orders'] = Order.objects.filter(status='pending').count()
        else:
            context['pending_orders'] = Order.objects.filter(
                event__manager=self.request.user, 
                status='pending'
            ).count()
        
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
        context['available_venues'] = Venue.objects.filter(is_active=True).order_by('name')
        
        return context
    
    def form_valid(self, form):
        form.instance.manager = self.request.user
        action = self.request.POST.get('action', 'publish')
        form.instance.status = Event.Status.PUBLISHED if action == 'publish' else Event.Status.DRAFT
        response = super().form_valid(form)

        # Optional ticket tier inputs from create form.
        ticket_names = self.request.POST.getlist('ticket_name[]')
        ticket_prices = self.request.POST.getlist('ticket_price[]')
        ticket_quantities = self.request.POST.getlist('ticket_quantity[]')

        if not form.instance.is_free and ticket_names:
            from decimal import Decimal, InvalidOperation
            from .models import TicketPricing

            for index, name in enumerate(ticket_names):
                tier_name = (name or '').strip()
                if not tier_name:
                    continue

                price_raw = ticket_prices[index] if index < len(ticket_prices) else ''
                quantity_raw = ticket_quantities[index] if index < len(ticket_quantities) else ''

                try:
                    price = Decimal(str(price_raw))
                except (InvalidOperation, ValueError):
                    continue

                try:
                    quantity = int(quantity_raw)
                except (TypeError, ValueError):
                    continue

                if price < 0 or quantity <= 0:
                    continue

                TicketPricing.objects.get_or_create(
                    event=form.instance,
                    ticket_type='regular',
                    name=tier_name,
                    defaults={
                        'price': price,
                        'available_quantity': quantity,
                        'is_active': True,
                    }
                )

        if form.instance.status == Event.Status.PUBLISHED:
            messages.success(self.request, 'Event created and published successfully!')
        else:
            messages.success(self.request, 'Event saved as draft successfully!')
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
        completed_orders = event.orders.filter(payment__status='completed').select_related('user', 'payment')
        context['tickets_sold'] = completed_orders.aggregate(total=Sum('ticket_quantity'))['total'] or 0
        context['revenue'] = completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        context['recent_sales'] = completed_orders.order_by('-created_at')[:10]
        
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
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        event_id = self.kwargs.get('pk')
        event = get_object_or_404(Event, pk=event_id, status='published')
        kwargs['event'] = event
        return kwargs
    
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
        
        ticket = form.save(commit=False)
        ticket.total_price = ticket.unit_price * ticket.quantity
        ticket.save()
        
        # Redirect to checkout
        return redirect('payments:checkout', ticket_id=ticket.id)


class CategoryEventListView(ListView):
    """List events by category"""
    model = Event
    template_name = 'events/category_events.html'
    context_object_name = 'events'
    paginate_by = CONTENT_CARDS_PER_PAGE
    
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()

        completed_orders = event.orders.filter(payment__status='completed').select_related('user', 'payment')
        context['tickets_sold'] = completed_orders.aggregate(total=Sum('ticket_quantity'))['total'] or 0
        context['revenue'] = completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        context['orders_count'] = completed_orders.count()
        context['recent_orders'] = completed_orders.order_by('-created_at')[:10]

        reviews = event.reviews.filter(status='approved')
        context['reviews_count'] = reviews.count()
        context['avg_rating'] = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

        return context


# Category Management Views
class CategoryListView(HorizonPlannerRequiredMixin, ListView):
    """List all categories"""
    model = Category
    template_name = 'events/category_list.html'
    context_object_name = 'categories'
    paginate_by = CONTENT_CARDS_PER_PAGE


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


# Static Pages Views
class AboutView(TemplateView):
    """About page"""
    template_name = 'pages/about.html'


class PolicyView(TemplateView):
    """Privacy & Terms Policy page"""
    template_name = 'pages/policy.html'


class ContactView(TemplateView):
    """Contact page"""
    template_name = 'pages/contact.html'


class EventShowcaseView(TemplateView):
    """Showcase page with active, recent and featured events"""
    template_name = 'events/event_showcase.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()

        completed_filter = (
            Q(status=Event.Status.COMPLETED) |
            (Q(event_date__lt=today) & ~Q(status=Event.Status.CANCELLED))
        )

        context['active_events'] = paginate_queryset(
            self.request,
            Event.objects.filter(
                status=Event.Status.PUBLISHED,
                event_date__gte=today
            ).select_related('venue', 'category', 'manager').order_by('event_date', 'start_time'),
            page_param='active_page',
        )

        context['recently_done_events'] = paginate_queryset(
            self.request,
            Event.objects.filter(
                completed_filter
            ).select_related('venue', 'category', 'manager').order_by('-event_date', '-start_time'),
            page_param='recent_page',
        )

        context['special_bookmarked_events'] = paginate_queryset(
            self.request,
            Event.objects.filter(
                is_featured=True
            ).exclude(
                status=Event.Status.DRAFT
            ).select_related('venue', 'category', 'manager').order_by('-event_date', 'start_time'),
            page_param='featured_page',
        )

        context['active_pagination_query'] = build_query_string(self.request, ['active_page'])
        context['recent_pagination_query'] = build_query_string(self.request, ['recent_page'])
        context['featured_pagination_query'] = build_query_string(self.request, ['featured_page'])

        context['total_events_done'] = Event.objects.filter(completed_filter).count()
        context['total_active_events'] = Event.objects.filter(
            status=Event.Status.PUBLISHED,
            event_date__gte=today
        ).count()
        context['total_featured_events'] = Event.objects.filter(
            is_featured=True
        ).exclude(status=Event.Status.DRAFT).count()

        return context


class AdminEventActionsMixin(UserPassesTestMixin):
    """Mixin to require admin user"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_user


class DeactivateEventView(AdminEventActionsMixin, TemplateView):
    """Admin deactivate event view"""
    template_name = 'events/admin_deactivate_event.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_id = kwargs.get('event_id')
        event = get_object_or_404(Event, id=event_id)
        
        from apps.core.models import Notification
        context['event'] = event
        context['reasons'] = Notification.ActionReason.choices
        
        return context
    
    def post(self, request, *args, **kwargs):
        event_id = kwargs.get('event_id')
        event = get_object_or_404(Event, id=event_id)
        reason = request.POST.get('reason')
        message = request.POST.get('message', '')
        
        # Deactivate event
        event.is_active = False
        event.save()
        
        # Send notification to manager
        from apps.core.models import Notification
        Notification.objects.create(
            recipient=event.manager,
            admin_user=request.user,
            notification_type=Notification.NotificationType.EVENT_DEACTIVATED,
            reason=reason,
            subject=f'Your Event "{event.title}" Has Been Deactivated',
            message=f"Your event has been deactivated by the admin.\n\nReason: {reason}\n\nMessage: {message}\n\nPlease contact support for more information.",
            event=event,
            details={
                'event_title': event.title,
                'event_id': event.id,
                'reason': reason,
                'admin_message': message
            }
        )
        
        messages.success(request, f'Event "{event.title}" has been deactivated and notification sent to manager.')
        return redirect('events:manager_dashboard')


class DeleteEventView(AdminEventActionsMixin, TemplateView):
    """Admin delete event view"""
    template_name = 'events/admin_delete_event.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_id = kwargs.get('event_id')
        event = get_object_or_404(Event, id=event_id)
        
        from apps.core.models import Notification
        context['event'] = event
        context['reasons'] = Notification.ActionReason.choices
        
        return context
    
    def post(self, request, *args, **kwargs):
        event_id = kwargs.get('event_id')
        event = get_object_or_404(Event, id=event_id)
        reason = request.POST.get('reason')
        message = request.POST.get('message', '')
        event_title = event.title
        event_manager = event.manager
        
        # Send notification before deleting
        from apps.core.models import Notification
        Notification.objects.create(
            recipient=event_manager,
            admin_user=request.user,
            notification_type=Notification.NotificationType.EVENT_DELETED,
            reason=reason,
            subject=f'Your Event "{event_title}" Has Been Deleted',
            message=f"Your event has been deleted by the admin.\n\nReason: {reason}\n\nMessage: {message}\n\nPlease contact support for more information.",
            details={
                'event_title': event_title,
                'event_id': event_id,
                'reason': reason,
                'admin_message': message
            }
        )
        
        # Delete event
        event.delete()
        
        messages.success(request, f'Event has been deleted and notification sent to manager.')
        return redirect('events:manager_dashboard')
