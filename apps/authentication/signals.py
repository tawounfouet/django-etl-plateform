from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from .models import CustomUser, UserProfile, UserSession


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile instance when a new CustomUser is created.
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile when the CustomUser is saved.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Handle user login events.
    """
    # Update last login time
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])
    
    # Update or create user session
    session_key = request.session.session_key
    if session_key:
        session, created = UserSession.objects.get_or_create(
            user=user,
            session_key=session_key,
            defaults={
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'is_active': True
            }
        )
        
        if not created:
            # Update existing session
            session.last_activity = timezone.now()
            session.is_active = True
            session.save(update_fields=['last_activity', 'is_active'])


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """
    Handle user logout events.
    """
    if user and hasattr(request, 'session'):
        session_key = request.session.session_key
        if session_key:
            try:
                session = UserSession.objects.get(
                    user=user,
                    session_key=session_key
                )
                session.is_active = False
                session.save(update_fields=['is_active'])
            except UserSession.DoesNotExist:
                pass


@receiver(post_delete, sender=CustomUser)
def cleanup_user_data(sender, instance, **kwargs):
    """
    Clean up user-related data when a user is deleted.
    """
    # Delete user sessions
    UserSession.objects.filter(user=instance).delete()
    
    # Additional cleanup can be added here for other user-related data
    # For example: delete user files, clear cache, etc.


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
