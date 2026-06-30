from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, Value, FloatField, DecimalField, IntegerField
from django.db.models.functions import Coalesce

from apps.users.models import User, RoleUpgradeRequest
from apps.events.models import Event
from apps.venues.models import Venue
from apps.payments.models import Payment
from apps.reviews.models import Review, Comment


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin role"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_user


# Stub views for analytics app
class PlatformAnalyticsView(AdminRequiredMixin, TemplateView):
    template_name = 'analytics/platform_analytics.html'

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'analytics/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        today = timezone.localdate()

        total_users = User.objects.count()
        total_events = Event.objects.count()
        total_venues = Venue.objects.count()
        platform_revenue = Payment.objects.filter(status=Payment.Status.COMPLETED).aggregate(
            total=Coalesce(
                Sum('amount'),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )['total']

        new_users_this_month = User.objects.filter(date_joined__gte=month_start).count()
        user_growth_percentage = round((new_users_this_month / total_users) * 100, 1) if total_users else 0

        active_events = Event.objects.filter(
            status=Event.Status.PUBLISHED,
            event_date__gte=today
        ).count()
        events_this_month = Event.objects.filter(created_at__gte=month_start).count()

        pending_role_requests = RoleUpgradeRequest.objects.filter(
            status=RoleUpgradeRequest.Status.PENDING
        ).count()
        pending_reviews = Review.objects.filter(status=Review.Status.PENDING).count() + Comment.objects.filter(
            status=Comment.Status.PENDING
        ).count()

        top_events = Event.objects.select_related('venue').annotate(
            annotated_tickets_sold=Coalesce(
                Sum('orders__ticket_quantity', filter=Q(orders__payment__status=Payment.Status.COMPLETED)),
                Value(0, output_field=IntegerField()),
                output_field=IntegerField()
            ),
            revenue=Coalesce(
                Sum('payments__amount', filter=Q(payments__status=Payment.Status.COMPLETED)),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            ),
            average_rating=Coalesce(
                Avg('reviews__rating', filter=Q(reviews__status='approved')),
                Value(0.0),
                output_field=FloatField()
            )
        ).order_by('-annotated_tickets_sold', '-revenue')[:8]

        recent_activities = []

        for user in User.objects.order_by('-date_joined')[:4]:
            recent_activities.append({
                'activity_type': 'user_registered',
                'description': f'New user registered: {user.username}',
                'created_at': user.date_joined,
            })

        for event in Event.objects.select_related('manager').order_by('-created_at')[:4]:
            recent_activities.append({
                'activity_type': 'event_created',
                'description': f'Event created: {event.title}',
                'created_at': event.created_at,
            })

        for venue in Venue.objects.select_related('manager').order_by('-created_at')[:3]:
            recent_activities.append({
                'activity_type': 'venue_added',
                'description': f'Venue listed: {venue.name}',
                'created_at': venue.created_at,
            })

        for req in RoleUpgradeRequest.objects.select_related('user').order_by('-created_at')[:3]:
            recent_activities.append({
                'activity_type': 'role_request',
                'description': f'Role request from {req.user.username} to {req.get_requested_role_display()}',
                'created_at': req.created_at,
            })

        recent_activities = sorted(recent_activities, key=lambda item: item['created_at'], reverse=True)[:12]

        context.update({
            'total_users': total_users,
            'total_events': total_events,
            'total_venues': total_venues,
            'platform_revenue': platform_revenue,
            'new_users_this_month': new_users_this_month,
            'user_growth_percentage': user_growth_percentage,
            'active_events': active_events,
            'events_this_month': events_this_month,
            'pending_role_requests': pending_role_requests,
            'pending_reviews': pending_reviews,
            'reported_issues': 0,
            'recent_activities': recent_activities,
            'top_events': top_events,
        })
        return context

class UserActivityView(AdminRequiredMixin, TemplateView):
    template_name = 'analytics/user_activity.html'

class ExportEventDataView(AdminRequiredMixin, TemplateView):
    template_name = 'analytics/export_events.html'

class ExportUserDataView(AdminRequiredMixin, TemplateView):
    template_name = 'analytics/export_users.html'

class ExportRevenueDataView(AdminRequiredMixin, TemplateView):
    template_name = 'analytics/export_revenue.html'

class RevenueChartDataView(AdminRequiredMixin, TemplateView):
    template_name = 'analytics/revenue_chart.html'

class UserGrowthDataView(AdminRequiredMixin, TemplateView):
    template_name = 'analytics/user_growth.html'

class EventStatsDataView(AdminRequiredMixin, TemplateView):
    template_name = 'analytics/event_stats.html'
