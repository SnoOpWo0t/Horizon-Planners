from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from apps.core.pagination import CONTENT_CARDS_PER_PAGE, build_query_string
from .models import Order, Payment
from apps.events.models import Ticket, Event
from apps.venues.models import VenueBookingRequest
import random
import string


class ManagerRequiredMixin(UserPassesTestMixin):
    """Mixin to require Horizon Planner or Admin"""
    def test_func(self):
        return (self.request.user.is_authenticated and 
                (self.request.user.is_horizon_planner or self.request.user.is_admin_user))


class ManagerOrdersView(ManagerRequiredMixin, ListView):
    """View all orders for manager's events"""
    template_name = 'payments/manager_orders.html'
    context_object_name = 'orders'
    paginate_by = CONTENT_CARDS_PER_PAGE
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            # Admin sees all orders
            orders = Order.objects.all().select_related('event', 'user', 'payment').order_by('-created_at')
        else:
            # Manager sees only orders for their events
            orders = Order.objects.filter(
                event__manager=user
            ).select_related('event', 'user', 'payment').order_by('-created_at')
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            orders = orders.filter(status=status)
        
        return orders
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_admin_user:
            context['pending_count'] = Order.objects.filter(status='pending').count()
            context['confirmed_count'] = Order.objects.filter(status='confirmed').count()
            context['total_revenue'] = sum(o.total_amount for o in Order.objects.all())
        else:
            context['pending_count'] = Order.objects.filter(
                event__manager=user, status='pending'
            ).count()
            context['confirmed_count'] = Order.objects.filter(
                event__manager=user, status='confirmed'
            ).count()
            context['total_revenue'] = sum(
                o.total_amount for o in Order.objects.filter(event__manager=user)
            )
        
        context['current_status'] = self.request.GET.get('status', 'all')
        context['pagination_query'] = build_query_string(self.request, ['page'])
        
        return context


class ManageOrderDetailView(ManagerRequiredMixin, TemplateView):
    """Manager view of specific order"""
    template_name = 'payments/manage_order_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_number = kwargs.get('order_number')
        order = get_object_or_404(Order, order_number=order_number)
        
        # Check permission
        if not self.request.user.is_admin_user and order.event.manager != self.request.user:
            raise PermissionError("Not authorized")
        
        context['order'] = order
        context['payment'] = order.payment
        context['event'] = order.event
        context['user'] = order.user
        
        return context


class ConfirmOrderView(ManagerRequiredMixin, View):
    """Confirm an order"""
    
    def post(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        
        # Check permission
        if not request.user.is_admin_user and order.event.manager != request.user:
            messages.error(request, 'Not authorized')
            return redirect('payments:manager_orders')
        
        order.status = 'confirmed'
        order.payment.status = 'completed'
        order.save()
        order.payment.save()
        
        # Notify the buyer
        from apps.core.models import Notification
        ticket_url = f"/payments/order/{order.id}/ticket/"
        Notification.objects.create(
            recipient=order.user,
            notification_type=Notification.NotificationType.OTHER,
            subject=f"Booking Accepted: {order.event.title}",
            message=f"Your booking for '{order.event.title}' has been accepted! You can now download your ticket.",
            event=order.event,
            details={'action_url': ticket_url}
        )
        
        messages.success(request, f'Order {order.order_number} confirmed!')
        return redirect('payments:manage_order_detail', order_number=order.order_number)


class DeclineOrderView(ManagerRequiredMixin, View):
    """Decline an order"""
    
    def post(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        reason = request.POST.get('reason', 'No reason provided')
        
        # Check permission
        if not request.user.is_admin_user and order.event.manager != request.user:
            messages.error(request, 'Not authorized')
            return redirect('payments:manager_orders')
        
        order.status = 'cancelled'
        order.payment.status = 'failed'
        order.payment.notes = reason
        order.save()
        order.payment.save()
        
        messages.success(request, f'Order {order.order_number} declined!')
        return redirect('payments:manage_order_detail', order_number=order.order_number)





class CheckoutView(LoginRequiredMixin, TemplateView):
    """Checkout view with payment method selection (COD only enabled)"""
    template_name = 'payments/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket_id = self.kwargs.get('ticket_id')
        ticket = get_object_or_404(Ticket, id=ticket_id, buyer=self.request.user)
        
        context['ticket'] = ticket
        context['event'] = ticket.event
        context['user'] = self.request.user
        
        # Only show COD as available payment method
        context['payment_methods'] = [
            {'value': 'cod', 'label': 'Cash on Delivery (COD)', 'enabled': True}
        ]
        
        return context
    
    def post(self, request, *args, **kwargs):
        ticket_id = kwargs.get('ticket_id')
        ticket = get_object_or_404(Ticket, id=ticket_id, buyer=request.user)
        payment_method = request.POST.get('payment_method')
        
        # Only COD allowed
        if payment_method != 'cod':
            messages.error(request, 'Only Cash on Delivery is available right now.')
            return redirect('payments:checkout', ticket_id=ticket_id)
        
        # Create payment and order
        payment = Payment.objects.create(
            user=request.user,
            event=ticket.event,
            amount=ticket.total_price,
            payment_method='cod',
            status='pending'
        )
        
        # Create order
        order_number = self._generate_order_number()
        order = Order.objects.create(
            order_number=order_number,
            payment=payment,
            user=request.user,
            event=ticket.event,
            ticket_quantity=ticket.quantity,
            unit_price=ticket.unit_price,
            total_amount=ticket.total_price,
            customer_name=request.user.get_full_name() or request.user.username,
            customer_email=request.user.email,
            customer_phone=getattr(request.user, 'phone', '')
        )
        
        # Notify the Event Manager (Horizon Planner)
        from apps.core.models import Notification
        Notification.objects.create(
            recipient=ticket.event.manager,
            notification_type=Notification.NotificationType.NEW_BOOKING,
            subject=f"New Ticket Booking: {ticket.event.title}",
            message=f"{request.user.username} has booked {ticket.quantity} ticket(s) for your event '{ticket.event.title}'. Order #{order.order_number}",
            event=ticket.event,
            details={'order_id': order.id, 'order_number': order.order_number}
        )
        
        # Redirect to confirmation
        return redirect('payments:checkout_confirm', order_id=order.id)
    
    def _generate_order_number(self):
        """Generate unique order number"""
        while True:
            order_num = 'ORD' + ''.join(random.choices(string.digits, k=8))
            if not Order.objects.filter(order_number=order_num).exists():
                return order_num


class CheckoutConfirmView(LoginRequiredMixin, TemplateView):
    """Order confirmation page"""
    template_name = 'payments/checkout_confirm.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id, user=self.request.user)
        
        context['order'] = order
        context['payment'] = order.payment
        context['event'] = order.event
        
        return context


class OrderConfirmedView(LoginRequiredMixin, TemplateView):
    """Order confirmed page (when admin approves)"""
    template_name = 'payments/order_confirmed.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id, user=self.request.user)
        
        context['order'] = order
        context['payment'] = order.payment
        context['event'] = order.event
        
        return context


class OrderDeclinedView(LoginRequiredMixin, TemplateView):
    """Order declined page"""
    template_name = 'payments/order_declined.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id, user=self.request.user)
        
        context['order'] = order
        context['payment'] = order.payment
        context['event'] = order.event
        
        return context


class ProcessPaymentView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/process_payment.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_id = kwargs.get('event_id')
        from apps.events.models import Event
        event = get_object_or_404(Event, id=event_id, status='published')
        
        context['event'] = event
        
        return context

class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/payment_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_id = kwargs.get('payment_id')
        payment = get_object_or_404(Payment, id=payment_id, user=self.request.user)
        
        context['payment'] = payment
        context['order'] = payment.order
        
        return context

class PaymentFailedView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/payment_failed.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_id = kwargs.get('payment_id')
        payment = get_object_or_404(Payment, id=payment_id, user=self.request.user)
        
        context['payment'] = payment
        context['order'] = payment.order
        
        return context

class TicketDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/ticket_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket_number = kwargs.get('ticket_number')
        ticket = get_object_or_404(Ticket, ticket_number=ticket_number, buyer=self.request.user)
        
        context['ticket'] = ticket
        context['event'] = ticket.event
        
        return context

class DownloadTicketView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/download_ticket.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket_number = kwargs.get('ticket_number')
        ticket = get_object_or_404(Ticket, ticket_number=ticket_number, buyer=self.request.user)
        
        context['ticket'] = ticket
        context['event'] = ticket.event
        
        return context

class OrderHistoryView(LoginRequiredMixin, ListView):
    template_name = 'payments/order_history.html'
    context_object_name = 'orders'
    paginate_by = CONTENT_CARDS_PER_PAGE

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).select_related('event', 'event__venue', 'event__category', 'payment').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['venue_bookings'] = VenueBookingRequest.objects.filter(
            requester=self.request.user
        ).order_by('-created_at')
        return context

class OrderDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/order_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_number = kwargs.get('order_number')
        order = get_object_or_404(Order, order_number=order_number, user=self.request.user)
        
        context['order'] = order
        context['payment'] = order.payment
        context['event'] = order.event
        
        return context

class RefundRequestView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/refund_request.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_id = kwargs.get('payment_id')
        payment = get_object_or_404(Payment, id=payment_id, user=self.request.user)
        
        context['payment'] = payment
        context['order'] = payment.order
        
        return context

class OrderTicketView(LoginRequiredMixin, TemplateView):
    """Download or view ticket for a confirmed order"""
    template_name = 'payments/order_ticket.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id, user=self.request.user)
        
        context['order'] = order
        context['event'] = order.event
        context['payment'] = order.payment
        return context
