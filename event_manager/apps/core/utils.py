"""
Utility functions for the Horizon Planner project
"""
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import uuid


def generate_qr_code(data, filename_prefix="qr"):
    """
    Generate a QR code for the given data
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.png"
    return ContentFile(buffer.read(), name=filename)


def generate_ticket_pdf(ticket):
    """
    Generate a PDF ticket for the given ticket object
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.darkblue,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    content = []
    
    # Title
    content.append(Paragraph("EVENT TICKET", title_style))
    content.append(Spacer(1, 20))
    
    # Event details
    event_info = f"""
    <b>Event:</b> {ticket.event.title}<br/>
    <b>Date:</b> {ticket.event.event_date}<br/>
    <b>Time:</b> {ticket.event.start_time} - {ticket.event.end_time}<br/>
    <b>Venue:</b> {ticket.event.venue.name}<br/>
    <b>Address:</b> {ticket.event.venue.address}<br/>
    """
    content.append(Paragraph(event_info, styles['Normal']))
    content.append(Spacer(1, 20))
    
    # Ticket details
    ticket_info = f"""
    <b>Ticket Number:</b> {ticket.ticket_number}<br/>
    <b>Ticket Type:</b> {ticket.get_ticket_type_display()}<br/>
    <b>Quantity:</b> {ticket.quantity}<br/>
    <b>Price:</b> ${ticket.total_price}<br/>
    <b>Buyer:</b> {ticket.buyer.get_full_name() or ticket.buyer.username}<br/>
    """
    content.append(Paragraph(ticket_info, styles['Normal']))
    content.append(Spacer(1, 20))
    
    # QR Code (if available)
    if ticket.qr_code:
        # Generate QR code image
        qr_img = generate_qr_code(ticket.qr_code)
        # Add to PDF (this is simplified - you'd need to handle the image properly)
        content.append(Paragraph("<b>QR Code for Entry:</b>", styles['Normal']))
    
    # Terms and conditions
    terms = """
    <b>Terms and Conditions:</b><br/>
    1. This ticket is non-transferable and non-refundable unless event is cancelled.<br/>
    2. Please arrive at least 30 minutes before event start time.<br/>
    3. Valid ID may be required for entry.<br/>
    4. Photography and recording may not be permitted during the event.<br/>
    """
    content.append(Spacer(1, 30))
    content.append(Paragraph(terms, styles['Normal']))
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    
    filename = f"ticket_{ticket.ticket_number}.pdf"
    return ContentFile(buffer.read(), name=filename)


def send_notification_email(user, subject, message, event=None):
    """
    Send notification email to user (placeholder for now)
    """
    # This would integrate with Django's email system
    # For now, just a placeholder function
    pass


def calculate_service_fee(amount, percentage=0.03):
    """
    Calculate service fee for ticket purchases
    """
    return round(amount * percentage, 2)


def calculate_tax(amount, tax_rate=0.08):
    """
    Calculate tax for ticket purchases
    """
    return round(amount * tax_rate, 2)


def format_currency(amount, currency_code='USD'):
    """
    Format currency for display
    """
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
    }
    symbol = symbols.get(currency_code, '$')
    return f"{symbol}{amount:,.2f}"


def slugify_event_title(title):
    """
    Create a URL-friendly slug from event title
    """
    import re
    slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug


def get_event_analytics_data(event):
    """
    Calculate analytics data for an event
    """
    from django.db.models import Sum, Count, Avg
    
    # Get related data
    tickets = event.tickets.filter(payment__status='completed')
    reviews = event.reviews.filter(status='approved')
    comments = event.comments.filter(status='approved')
    
    analytics = {
        'tickets_sold': tickets.aggregate(total=Sum('quantity'))['total'] or 0,
        'gross_revenue': tickets.aggregate(total=Sum('total_price'))['total'] or 0,
        'reviews_count': reviews.count(),
        'average_rating': reviews.aggregate(avg=Avg('rating'))['avg'] or 0,
        'comments_count': comments.count(),
        'attendance_rate': (event.total_seats - event.available_seats) / event.total_seats * 100 if event.total_seats > 0 else 0,
    }
    
    return analytics
