from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # Home/Event listing
    path('', views.EventListView.as_view(), name='home'),
    path('events/', views.EventListView.as_view(), name='event_list'),
    
    # Event details and booking
    path('event/<slug:slug>/', views.EventDetailView.as_view(), name='event_detail'),
    path('event/<slug:slug>/book/', views.BookTicketView.as_view(), name='book_ticket'),
    
    # Event management (for Horizon Planners)
    path('manage/', views.HorizonPlannerDashboardView.as_view(), name='manager_dashboard'),
    path('manage/create/', views.CreateEventView.as_view(), name='create_event'),
    path('manage/event/<slug:slug>/', views.ManageEventView.as_view(), name='manage_event'),
    path('manage/event/<slug:slug>/edit/', views.EditEventView.as_view(), name='edit_event'),
    path('manage/event/<slug:slug>/delete/', views.DeleteEventView.as_view(), name='delete_event'),
    
    # Analytics
    path('manage/analytics/', views.EventAnalyticsView.as_view(), name='event_analytics'),
    path('manage/event/<slug:slug>/analytics/', views.EventDetailAnalyticsView.as_view(), name='event_detail_analytics'),
    
    # Categories
    path('category/<int:pk>/', views.CategoryEventListView.as_view(), name='category_events'),
    path('manage/categories/', views.CategoryListView.as_view(), name='category_list'),
    path('manage/categories/create/', views.CreateCategoryView.as_view(), name='create_category'),
    path('manage/categories/<int:pk>/edit/', views.EditCategoryView.as_view(), name='edit_category'),
    path('manage/categories/<int:pk>/delete/', views.DeleteCategoryView.as_view(), name='delete_category'),
]
