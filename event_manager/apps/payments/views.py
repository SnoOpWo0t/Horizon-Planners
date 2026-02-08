from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Order
from apps.venues.models import VenueBookingRequest


# Stub views for payments app
class ProcessPaymentView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/process_payment.html'

class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/payment_success.html'

class PaymentFailedView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/payment_failed.html'

class TicketDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/ticket_detail.html'

class DownloadTicketView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/download_ticket.html'

class OrderHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/order_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get event orders
        context['orders'] = Order.objects.filter(user=user).order_by('-created_at')
        
        # Get venue bookings
        context['venue_bookings'] = VenueBookingRequest.objects.filter(
            requester=user
        ).order_by('-created_at')
        
        return context

class OrderDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/order_detail.html'

class RefundRequestView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/refund_request.html'
