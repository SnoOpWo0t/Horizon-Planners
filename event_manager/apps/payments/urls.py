from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Manager order management
    path('manager/orders/', views.ManagerOrdersView.as_view(), name='manager_orders'),
    path('manager/order/<str:order_number>/', views.ManageOrderDetailView.as_view(), name='manage_order_detail'),
    path('manager/order/<int:order_id>/confirm/', views.ConfirmOrderView.as_view(), name='confirm_order'),
    path('manager/order/<int:order_id>/decline/', views.DeclineOrderView.as_view(), name='decline_order'),
    
    # Checkout flow
    path('checkout/<int:ticket_id>/', views.CheckoutView.as_view(), name='checkout'),
    path('checkout/confirm/<int:order_id>/', views.CheckoutConfirmView.as_view(), name='checkout_confirm'),
    path('order/confirmed/<int:order_id>/', views.OrderConfirmedView.as_view(), name='order_confirmed'),
    path('order/declined/<int:order_id>/', views.OrderDeclinedView.as_view(), name='order_declined'),
    
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
