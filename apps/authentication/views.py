from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    UserProfileForm,
    PasswordChangeForm
)
from .models import CustomUser, UserProfile, UserSession


class RegisterView(CreateView):
    """
    User registration view.
    """
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'authentication/register.html'
    success_url = reverse_lazy('authentication:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Account created successfully! You can now log in.'
        )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Please correct the errors below.'
        )
        return super().form_invalid(form)


def login_view(request):
    """
    Custom login view using email authentication.
    """
    if request.user.is_authenticated:
        return redirect('ui:dashboard')

    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Create user session record
            UserSession.objects.create(
                user=user,
                session_key=request.session.session_key,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Welcome back, {user.get_short_name()}!')
            
            # Redirect to next page or dashboard
            next_page = request.GET.get('next', 'ui:dashboard')
            return redirect(next_page)
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'authentication/login.html', {'form': form})


@login_required
def logout_view(request):
    """
    Logout view that handles session cleanup.
    """
    # Mark user session as inactive
    try:
        session = UserSession.objects.get(
            user=request.user,
            session_key=request.session.session_key
        )
        session.is_active = False
        session.save()
    except UserSession.DoesNotExist:
        pass
    
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('authentication:login')


@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    """
    User profile view for viewing and editing profile information.
    """
    template_name = 'authentication/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        context.update({
            'user': user,
            'profile': profile,
            'profile_form': UserProfileForm(instance=profile),
            'password_form': PasswordChangeForm(user=user)
        })
        return context


@login_required
def update_profile(request):
    """
    Update user profile information via AJAX.
    """
    if request.method == 'POST':
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Profile updated successfully!'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def change_password(request):
    """
    Change user password via AJAX.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        
        if form.is_valid():
            form.save()
            # Update session auth hash to prevent logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            
            return JsonResponse({
                'success': True,
                'message': 'Password changed successfully!'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def user_sessions(request):
    """
    View user's active sessions for security monitoring.
    """
    sessions = UserSession.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-last_activity')
    
    return render(request, 'authentication/sessions.html', {
        'sessions': sessions,
        'current_session': request.session.session_key
    })


@login_required
def revoke_session(request, session_id):
    """
    Revoke a specific user session.
    """
    try:
        session = UserSession.objects.get(
            id=session_id,
            user=request.user
        )
        session.is_active = False
        session.save()
        
        messages.success(request, 'Session revoked successfully.')
    except UserSession.DoesNotExist:
        messages.error(request, 'Session not found.')
    
    return redirect('authentication:sessions')


def get_client_ip(request):
    """
    Get the client IP address from the request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# API Views for mobile/external authentication
@csrf_exempt
def api_login(request):
    """
    API endpoint for authentication (for mobile apps or external services).
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return JsonResponse({
                    'success': False,
                    'message': 'Email and password are required'
                }, status=400)
            
            user = authenticate(username=email, password=password)
            if user:
                # Generate or get user token (you might want to use DRF tokens)
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'permissions': {
                            'can_create_pipelines': user.can_create_pipelines,
                            'can_modify_pipelines': user.can_modify_pipelines,
                            'can_execute_pipelines': user.can_execute_pipelines,
                            'can_view_monitoring': user.can_view_monitoring,
                            'can_manage_connectors': user.can_manage_connectors,
                        }
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid credentials'
                }, status=401)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)
