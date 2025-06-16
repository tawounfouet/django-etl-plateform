from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import EmailValidator
from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model following Django best practices.
    Uses email as the unique identifier instead of username.
    """
    
    # Email as unique identifier
    email = models.EmailField(
        'Email address',
        unique=True,
        validators=[EmailValidator()],
        error_messages={
            'unique': "A user with that email already exists.",
        },
    )
    
    # Personal information
    first_name = models.CharField('First name', max_length=150, blank=True)
    last_name = models.CharField('Last name', max_length=150, blank=True)
    
    # User status fields
    is_active = models.BooleanField(
        'Active',
        default=True,
        help_text='Designates whether this user should be treated as active. '
                  'Unselect this instead of deleting accounts.'
    )
    is_staff = models.BooleanField(
        'Staff status',
        default=False,
        help_text='Designates whether the user can log into this admin site.'
    )
    
    # Timestamps
    date_joined = models.DateTimeField('Date joined', default=timezone.now)
    last_login = models.DateTimeField('Last login', blank=True, null=True)
    
    # ETL Platform specific fields
    department = models.CharField(
        'Department',
        max_length=100,
        blank=True,
        help_text='User department or team'
    )
    
    job_title = models.CharField(
        'Job Title',
        max_length=100,
        blank=True,
        help_text='User job title or role'
    )
    
    phone = models.CharField(
        'Phone number',
        max_length=20,
        blank=True,
        help_text='Contact phone number'
    )
    
    # Permissions for ETL operations
    can_create_pipelines = models.BooleanField(
        'Can create pipelines',
        default=False,
        help_text='Designates whether the user can create ETL pipelines.'
    )
    
    can_modify_pipelines = models.BooleanField(
        'Can modify pipelines',
        default=False,
        help_text='Designates whether the user can modify existing ETL pipelines.'
    )
    
    can_execute_pipelines = models.BooleanField(
        'Can execute pipelines',
        default=True,
        help_text='Designates whether the user can execute ETL pipelines.'
    )
    
    can_view_monitoring = models.BooleanField(
        'Can view monitoring',
        default=True,
        help_text='Designates whether the user can view monitoring dashboards.'
    )
    
    can_manage_connectors = models.BooleanField(
        'Can manage connectors',
        default=False,
        help_text='Designates whether the user can manage data connectors.'
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        db_table = 'auth_user'  # Keep the same table name for easier migration
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active', 'is_staff']),
            models.Index(fields=['date_joined']),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def has_etl_permission(self, permission):
        """
        Check if user has specific ETL permission.
        """
        permission_map = {
            'create_pipelines': self.can_create_pipelines,
            'modify_pipelines': self.can_modify_pipelines,
            'execute_pipelines': self.can_execute_pipelines,
            'view_monitoring': self.can_view_monitoring,
            'manage_connectors': self.can_manage_connectors,
        }
        return permission_map.get(permission, False)


class UserProfile(models.Model):
    """
    Extended user profile information.
    Separate model to keep the User model lean and allow for future extensions.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Profile picture
    avatar = models.ImageField(
        'Avatar',
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text='User profile picture'
    )
    
    # Preferences
    timezone = models.CharField(
        'Timezone',
        max_length=50,
        default='UTC',
        help_text='User preferred timezone'
    )
    
    language = models.CharField(
        'Language',
        max_length=10,
        default='en',
        choices=[
            ('en', 'English'),
            ('fr', 'French'),
            ('es', 'Spanish'),
        ],
        help_text='User preferred language'
    )
    
    # Notification preferences
    email_notifications = models.BooleanField(
        'Email notifications',
        default=True,
        help_text='Receive email notifications'
    )
    
    pipeline_notifications = models.BooleanField(
        'Pipeline notifications',
        default=True,
        help_text='Receive notifications about pipeline execution'
    )
    
    # Bio and additional info
    bio = models.TextField(
        'Biography',
        max_length=500,
        blank=True,
        help_text='Brief description about the user'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.email} Profile"


class UserSession(models.Model):
    """
    Track user sessions for security and monitoring purposes.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.session_key[:8]}..."
