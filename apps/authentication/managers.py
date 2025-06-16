from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom user manager for CustomUser model.
    Manages user creation with email as the unique identifier.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with an email and password.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with an email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        # Set ETL permissions for superuser
        extra_fields.setdefault('can_create_pipelines', True)
        extra_fields.setdefault('can_modify_pipelines', True)
        extra_fields.setdefault('can_execute_pipelines', True)
        extra_fields.setdefault('can_view_monitoring', True)
        extra_fields.setdefault('can_manage_connectors', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        """
        Get user by email (natural key).
        """
        return self.get(email__iexact=email)
