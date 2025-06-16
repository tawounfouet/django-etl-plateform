from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils import timezone
from .models import UserSession


class SessionTimeoutMiddleware(MiddlewareMixin):
    """
    Middleware to handle session timeout and cleanup.
    """
    
    def process_request(self, request):
        if request.user.is_authenticated:
            session_key = request.session.session_key
            
            if session_key:
                try:
                    user_session = UserSession.objects.get(
                        user=request.user,
                        session_key=session_key,
                        is_active=True
                    )
                    
                    # Update last activity
                    user_session.last_activity = timezone.now()
                    user_session.save(update_fields=['last_activity'])
                    
                except UserSession.DoesNotExist:
                    # Session doesn't exist or is inactive, logout user
                    logout(request)
                    return redirect('authentication:login')
        
        return None


class IPRestrictionMiddleware(MiddlewareMixin):
    """
    Middleware to restrict access based on IP addresses (if configured).
    """
    
    def process_request(self, request):
        # This can be extended to check against allowed IP ranges
        # For now, it's a placeholder for future security enhancements
        return None


class UserActivityMiddleware(MiddlewareMixin):
    """
    Middleware to track user activity for analytics and security.
    """
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Update user's last activity
            request.user.last_login = timezone.now()
            request.user.save(update_fields=['last_login'])
        
        return None
