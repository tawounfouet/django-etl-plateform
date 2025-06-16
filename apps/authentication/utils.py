import secrets
import string
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def generate_random_password(length=12):
    """
    Generate a secure random password.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_username_from_email(email):
    """
    Generate a username from email address.
    """
    return email.split('@')[0].lower()


def send_password_reset_email(user, request):
    """
    Send password reset email to user.
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    reset_url = request.build_absolute_uri(
        f'/auth/password-reset-confirm/{uid}/{token}/'
    )
    
    subject = 'Password Reset - ETL Platform'
    message = render_to_string('authentication/emails/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
        'site_name': 'ETL Platform'
    })
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=message
    )


def send_welcome_email(user):
    """
    Send welcome email to new user.
    """
    subject = 'Welcome to ETL Platform'
    message = render_to_string('authentication/emails/welcome.html', {
        'user': user,
        'site_name': 'ETL Platform'
    })
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=message
    )


def validate_password_strength(password):
    """
    Validate password strength beyond Django's default validators.
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter.")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter.")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit.")
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        errors.append("Password must contain at least one special character.")
    
    return errors


def check_user_permissions(user, required_permissions):
    """
    Check if user has required ETL permissions.
    
    Args:
        user: CustomUser instance
        required_permissions: list of permission strings
        
    Returns:
        bool: True if user has all required permissions
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    for permission in required_permissions:
        if not user.has_etl_permission(permission):
            return False
    
    return True


def get_user_role_display(user):
    """
    Get a human-readable role display for the user.
    """
    if user.is_superuser:
        return "Super Administrator"
    elif user.is_staff:
        return "Administrator"
    elif user.can_create_pipelines and user.can_modify_pipelines:
        return "Pipeline Developer"
    elif user.can_execute_pipelines:
        return "Pipeline Operator"
    elif user.can_view_monitoring:
        return "Viewer"
    else:
        return "Basic User"


def create_user_with_profile(email, first_name, last_name, **kwargs):
    """
    Create a user with associated profile in a single transaction.
    """
    from django.db import transaction
    from .models import UserProfile
    
    with transaction.atomic():
        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **kwargs
        )
        
        # Profile is created automatically via signals
        # but we can customize it here if needed
        profile = user.profile
        profile.save()
        
        return user


def deactivate_user_sessions(user):
    """
    Deactivate all active sessions for a user.
    """
    from .models import UserSession
    
    UserSession.objects.filter(
        user=user,
        is_active=True
    ).update(is_active=False)


def get_user_activity_summary(user, days=30):
    """
    Get user activity summary for the last N days.
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import UserSession
    
    start_date = timezone.now() - timedelta(days=days)
    
    sessions = UserSession.objects.filter(
        user=user,
        created_at__gte=start_date
    )
    
    return {
        'total_sessions': sessions.count(),
        'active_sessions': sessions.filter(is_active=True).count(),
        'last_login': user.last_login,
        'unique_ips': sessions.values('ip_address').distinct().count(),
    }
