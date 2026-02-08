from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, DetailView, UpdateView, ListView, View
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from .models import User, RoleUpgradeRequest
from .forms import CustomUserCreationForm, ProfileUpdateForm, RoleUpgradeRequestForm


class CustomLoginView(LoginView):
    """Custom login view"""
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('events:home')


class CustomLogoutView(View):
    """Custom logout view with redirect and message"""
    
    def post(self, request):
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('events:home')
    
    def get(self, request):
        # Handle GET requests to logout (from navigation links)
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('events:home')


class SignUpView(CreateView):
    """User registration view"""
    form_class = CustomUserCreationForm
    template_name = 'users/signup.html'
    success_url = reverse_lazy('events:home')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        messages.success(self.request, f'Welcome to EventEase, {username}!')
        return response


class ProfileView(LoginRequiredMixin, DetailView):
    """User profile view"""
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile"""
    model = User
    form_class = ProfileUpdateForm
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')
    
    def get_object(self):
        return self.request.user


class RoleUpgradeRequestView(LoginRequiredMixin, CreateView):
    """Request role upgrade"""
    model = RoleUpgradeRequest
    form_class = RoleUpgradeRequestForm
    template_name = 'users/request_upgrade.html'
    success_url = reverse_lazy('users:profile')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Your role upgrade request has been submitted for review.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if user already has pending requests
        context['pending_requests'] = RoleUpgradeRequest.objects.filter(
            user=self.request.user,
            status='pending'
        )
        return context


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin role"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_user


class RoleRequestListView(AdminRequiredMixin, ListView):
    """List all role upgrade requests for admin review"""
    model = RoleUpgradeRequest
    template_name = 'users/role_requests.html'
    context_object_name = 'requests'
    paginate_by = 20
    
    def get_queryset(self):
        return RoleUpgradeRequest.objects.all().order_by('-created_at')


class ApproveRoleRequestView(AdminRequiredMixin, View):
    """Approve role upgrade request"""
    
    def post(self, request, pk):
        try:
            role_request = get_object_or_404(RoleUpgradeRequest, pk=pk)
            
            # Update user role
            user = role_request.user
            user.role = role_request.requested_role
            user.save()
            
            # Update request status
            role_request.status = 'approved'
            role_request.reviewed_by = request.user
            role_request.reviewed_at = timezone.now()
            role_request.review_notes = request.POST.get('review_notes', '')
            role_request.save()
            
            success_message = f'Role upgrade approved for {user.username}.'
            messages.success(request, success_message)
            
            # Always return JSON response for API consistency
            return JsonResponse({
                'success': True,
                'message': success_message,
                'user': user.username,
                'new_role': role_request.requested_role
            })
            
        except Exception as e:
            error_message = f'Error approving role request: {str(e)}'
            return JsonResponse({
                'success': False,
                'message': error_message
            }, status=400)


class RejectRoleRequestView(AdminRequiredMixin, View):
    """Reject role upgrade request"""
    
    def post(self, request, pk):
        try:
            role_request = get_object_or_404(RoleUpgradeRequest, pk=pk)
            
            # Update request status
            role_request.status = 'rejected'
            role_request.reviewed_by = request.user
            role_request.reviewed_at = timezone.now()
            role_request.review_notes = request.POST.get('review_notes', '')
            role_request.save()
            
            info_message = f'Role upgrade rejected for {role_request.user.username}.'
            messages.info(request, info_message)
            
            # Always return JSON response for API consistency
            return JsonResponse({
                'success': True,
                'message': info_message,
                'user': role_request.user.username
            })
            
        except Exception as e:
            error_message = f'Error rejecting role request: {str(e)}'
            return JsonResponse({
                'success': False,
                'message': error_message
            }, status=400)


class AdminSetupView(View):
    """Admin setup page for development/testing"""
    template_name = 'users/admin_setup.html'
    
    def get(self, request):
        context = {
            'admin_count': User.objects.filter(role=User.Role.ADMIN).count(),
            'total_users': User.objects.count(),
            'pending_requests': RoleUpgradeRequest.objects.filter(status='pending').count(),
            'total_requests': RoleUpgradeRequest.objects.count(),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        if 'create_admin' in request.POST:
            self.create_admin_user(request)
        elif 'create_test_data' in request.POST:
            self.create_test_data(request)
        
        return redirect('users:admin_setup')
    
    def create_admin_user(self, request):
        username = request.POST.get('admin_username')
        password = request.POST.get('admin_password')
        email = request.POST.get('admin_email')
        
        if User.objects.filter(username=username).exists():
            messages.warning(request, f'User "{username}" already exists!')
            return
        
        admin_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name='Admin',
            last_name='User',
            role=User.Role.ADMIN
        )
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        
        messages.success(request, f'Admin user "{username}" created successfully!')
    
    def create_test_data(self, request):
        # Create test users
        test_users = [
            {'username': 'john_doe', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'username': 'jane_smith', 'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'username': 'bob_wilson', 'email': 'bob@example.com', 'first_name': 'Bob', 'last_name': 'Wilson'},
        ]
        
        created_users = []
        for user_data in test_users:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password='password123',
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=User.Role.BASIC
                )
                created_users.append(user)
        
        # Create role upgrade requests
        requests_data = [
            {
                'username': 'john_doe',
                'role': RoleUpgradeRequest.RequestedRole.HORIZON_PLANNER,
                'reason': 'I have experience organizing events and would like to help organize events on this platform.'
            },
            {
                'username': 'jane_smith',
                'role': RoleUpgradeRequest.RequestedRole.VENUE_MANAGER,
                'reason': 'I own a banquet hall and would like to list my venue on this platform.'
            },
            {
                'username': 'bob_wilson',
                'role': RoleUpgradeRequest.RequestedRole.HORIZON_PLANNER,
                'reason': 'I am a professional event planner with 3 years of experience.'
            }
        ]
        
        created_requests = 0
        for req_data in requests_data:
            try:
                user = User.objects.get(username=req_data['username'])
                if not RoleUpgradeRequest.objects.filter(user=user, status='pending').exists():
                    RoleUpgradeRequest.objects.create(
                        user=user,
                        requested_role=req_data['role'],
                        reason=req_data['reason']
                    )
                    created_requests += 1
            except User.DoesNotExist:
                pass
        
        messages.success(request, f'Created {len(created_users)} test users and {created_requests} role requests!')
