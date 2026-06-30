from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    
    # Role management
    path('request-upgrade/', views.RoleUpgradeRequestView.as_view(), name='request_upgrade'),
    path('role-requests/', views.RoleRequestListView.as_view(), name='role_requests'),
    path('role-request/<int:pk>/approve/', views.ApproveRoleRequestView.as_view(), name='approve_role_request'),
    path('role-request/<int:pk>/reject/', views.RejectRoleRequestView.as_view(), name='reject_role_request'),
    
    # Admin setup (development only)
    path('admin-setup/', views.AdminSetupView.as_view(), name='admin_setup'),
]
