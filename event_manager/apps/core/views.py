from django.http import JsonResponse
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from .models import Notification


class UserNotificationsView(LoginRequiredMixin, View):
    """API view to get user's unread notifications"""
    
    def get(self, request):
        """Get unread notifications for current user"""
        notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).order_by('-created_at')
        
        unread_count = notifications.count()
        
        notifications_data = []
        for notif in notifications[:10]:  # Limit to last 10
            notifications_data.append({
                'id': notif.id,
                'subject': notif.subject,
                'message': notif.message,
                'type': notif.notification_type,
                'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'event_id': notif.event_id,
                'venue_id': notif.venue_id,
            })
        
        return JsonResponse({
            'unread_count': unread_count,
            'notifications': notifications_data
        })


class MarkNotificationReadView(LoginRequiredMixin, View):
    """API view to mark notification as read"""
    
    @method_decorator(require_POST)
    def post(self, request, notification_id):
        """Mark notification as read"""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=request.user
            )
            notification.mark_as_read()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)


class GetNotificationDetailView(LoginRequiredMixin, View):
    """API view to get notification detail and redirect URL"""
    
    def get(self, request, notification_id):
        """Get notification detail"""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=request.user
            )
            
            redirect_url = None
            
            # Determine redirect URL based on notification type
            if notification.notification_type in ['event_deactivated', 'event_deleted']:
                if notification.event:
                    redirect_url = f'/events/manage/{notification.event.slug}/'
            elif notification.notification_type in ['venue_deactivated', 'venue_deleted']:
                if notification.venue:
                    redirect_url = f'/venues/manage/{notification.venue.slug}/'
            elif notification.notification_type in ['new_comment', 'comment_reply']:
                if notification.event:
                    redirect_url = f'/reviews/event/{notification.event.id}/comments/'
            elif notification.notification_type == 'new_review':
                if notification.event:
                    redirect_url = f'/reviews/event/{notification.event.id}/all-reviews/'
                elif notification.venue:
                    redirect_url = f'/reviews/venue/{notification.venue.id}/all-reviews/'
            
            # Mark as read
            notification.mark_as_read()
            
            return JsonResponse({
                'success': True,
                'redirect_url': redirect_url,
                'notification': {
                    'subject': notification.subject,
                    'message': notification.message,
                    'type': notification.notification_type,
                }
            })
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)
