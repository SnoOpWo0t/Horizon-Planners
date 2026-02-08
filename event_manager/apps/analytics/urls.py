from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Platform-wide analytics (for admins)
    path('', views.PlatformAnalyticsView.as_view(), name='platform_analytics'),
    path('dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    
    # User activity tracking
    path('user-activity/', views.UserActivityView.as_view(), name='user_activity'),
    
    # Export data
    path('export/events/', views.ExportEventDataView.as_view(), name='export_event_data'),
    path('export/users/', views.ExportUserDataView.as_view(), name='export_user_data'),
    path('export/revenue/', views.ExportRevenueDataView.as_view(), name='export_revenue_data'),
    
    # API endpoints for charts/graphs
    path('api/revenue-chart/', views.RevenueChartDataView.as_view(), name='revenue_chart_data'),
    path('api/user-growth/', views.UserGrowthDataView.as_view(), name='user_growth_data'),
    path('api/event-stats/', views.EventStatsDataView.as_view(), name='event_stats_data'),
]
