from django.urls import path
from . import views

app_name = 'venues'

urlpatterns = [
    # Venue browsing
    path('', views.VenueListView.as_view(), name='venue_list'),
    path('venue/<slug:slug>/', views.VenueDetailView.as_view(), name='venue_detail'),
    
    # Venue management (for venue managers)
    path('manage/', views.VenueManagerDashboardView.as_view(), name='manager_dashboard'),
    path('manage/create/', views.CreateVenueView.as_view(), name='create_venue'),
    path('manage/venue/<slug:slug>/', views.ManageVenueView.as_view(), name='manage_venue'),
    path('manage/venue/<slug:slug>/edit/', views.EditVenueView.as_view(), name='edit_venue'),
    path('manage/venue/<slug:slug>/delete/', views.DeleteVenueView.as_view(), name='delete_venue'),
    
    # Venue booking management
    path('manage/bookings/', views.VenueBookingsView.as_view(), name='venue_bookings'),
    path('booking-request/<int:pk>/approve/', views.ApproveBookingRequestView.as_view(), name='approve_booking'),
    path('booking-request/<int:pk>/reject/', views.RejectBookingRequestView.as_view(), name='reject_booking'),
    
    # Availability management
    path('manage/availability/', views.ManageVenueAvailabilityView.as_view(), name='manage_availability'),
    
    # Analytics
    path('manage/analytics/', views.VenueAnalyticsView.as_view(), name='venue_analytics'),
    
    # For Horizon Planners to book venues
    path('book/<slug:slug>/', views.BookVenueView.as_view(), name='book_venue'),
]
