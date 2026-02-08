from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment processing
    path('process/<int:event_id>/', views.ProcessPaymentView.as_view(), name='process_payment'),
    path('success/<int:payment_id>/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('failed/<int:payment_id>/', views.PaymentFailedView.as_view(), name='payment_failed'),
    
    # Ticket management
    path('ticket/<str:ticket_number>/', views.TicketDetailView.as_view(), name='ticket_detail'),
    path('ticket/<str:ticket_number>/download/', views.DownloadTicketView.as_view(), name='download_ticket'),
    
    # Order history
    path('my-orders/', views.OrderHistoryView.as_view(), name='order_history'),
    path('order/<str:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
    
    # Refunds
    path('refund/<int:payment_id>/', views.RefundRequestView.as_view(), name='refund_request'),
]
