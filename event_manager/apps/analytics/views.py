from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin role"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_user


# Stub views for analytics app
class PlatformAnalyticsView(AdminRequiredMixin, TemplateView):
    template_name = 'analytics/platform_analytics.html'

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'analytics/admin_dashboard.html'

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
