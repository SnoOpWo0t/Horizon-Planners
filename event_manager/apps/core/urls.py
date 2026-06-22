from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Notifications API
    path('api/notifications/', views.UserNotificationsView.as_view(), name='user_notifications'),
    path('api/notifications/<int:notification_id>/mark-read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('api/notifications/<int:notification_id>/', views.GetNotificationDetailView.as_view(), name='notification_detail'),
]
