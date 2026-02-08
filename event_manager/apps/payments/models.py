from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel
import uuid


class Payment(TimeStampedModel):
    """Payment processing model"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'
        REFUNDED = 'refunded', 'Refunded'
    
    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = 'credit_card', 'Credit Card'
        DEBIT_CARD = 'debit_card', 'Debit Card'
        PAYPAL = 'paypal', 'PayPal'
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
    
    # Payment identification
    payment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    transaction_id = models.CharField(max_length=100, blank=True)  # External payment gateway ID
    
    # User and event details
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Gateway response data (store as JSON)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    processed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.payment_id} - ${self.amount} ({self.get_status_display()})"


class Order(TimeStampedModel):
    """Order model linking payment to tickets"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    order_number = models.CharField(max_length=20, unique=True)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='order')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='orders')
    
    # Order details
    ticket_quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Tax and fees
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Customer information
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_number} - {self.event.title}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            import random
            import string
            self.order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super().save(*args, **kwargs)


class Refund(TimeStampedModel):
    """Refund processing model"""
    
    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Requested'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        REJECTED = 'rejected', 'Rejected'
    
    class Reason(models.TextChoices):
        EVENT_CANCELLED = 'event_cancelled', 'Event Cancelled'
        CUSTOMER_REQUEST = 'customer_request', 'Customer Request'
        DUPLICATE_PAYMENT = 'duplicate_payment', 'Duplicate Payment'
        FRAUD = 'fraud', 'Fraud'
        OTHER = 'other', 'Other'
    
    refund_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    original_payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    
    # Refund details
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=20, choices=Reason.choices)
    reason_description = models.TextField(blank=True)
    
    # Status and processing
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='processed_refunds'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Gateway information
    gateway_refund_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund {self.refund_id} - ${self.refund_amount} ({self.get_status_display()})"
