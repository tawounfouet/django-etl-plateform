from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserProfile, UserSession


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """
    Custom User Admin interface.
    """
    model = CustomUser
    inlines = (UserProfileInline,)
    
    # Fields to display in the user list
    list_display = (
        'email',
        'first_name', 
        'last_name',
        'is_staff',
        'is_active',
        'date_joined',
        'department',
        'job_title'
    )
    
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'date_joined',
        'department',
        'can_create_pipelines',
        'can_modify_pipelines',
        'can_execute_pipelines',
    )
    
    search_fields = ('email', 'first_name', 'last_name', 'department')
    ordering = ('email',)
    
    # Fields for creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'is_staff',
                'is_active'
            ),
        }),
        (_('Personal info'), {
            'fields': ('department', 'job_title', 'phone')
        }),
        (_('ETL Permissions'), {
            'fields': (
                'can_create_pipelines',
                'can_modify_pipelines',
                'can_execute_pipelines',
                'can_view_monitoring',
                'can_manage_connectors',
            )
        }),
    )
    
    # Fields for editing an existing user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name',
                'last_name',
                'department',
                'job_title',
                'phone'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
        }),
        (_('ETL Permissions'), {
            'fields': (
                'can_create_pipelines',
                'can_modify_pipelines',
                'can_execute_pipelines',
                'can_view_monitoring',
                'can_manage_connectors',
            ),
            'classes': ('collapse',),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    User Profile Admin interface.
    """
    list_display = (
        'user',
        'timezone',
        'language',
        'email_notifications',
        'pipeline_notifications',
        'created_at'
    )
    
    list_filter = (
        'timezone',
        'language',
        'email_notifications',
        'pipeline_notifications',
        'created_at'
    )
    
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    
    fieldsets = (
        (_('User'), {
            'fields': ('user',)
        }),
        (_('Profile'), {
            'fields': ('avatar', 'bio')
        }),
        (_('Preferences'), {
            'fields': ('timezone', 'language')
        }),
        (_('Notifications'), {
            'fields': ('email_notifications', 'pipeline_notifications')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """
    User Session Admin interface for monitoring and security.
    """
    list_display = (
        'user',
        'session_key_short',
        'ip_address',
        'is_active',
        'created_at',
        'last_activity'
    )
    
    list_filter = (
        'is_active',
        'created_at',
        'last_activity'
    )
    
    search_fields = ('user__email', 'session_key', 'ip_address')
    readonly_fields = ('session_key', 'created_at', 'last_activity')
    
    def session_key_short(self, obj):
        return f"{obj.session_key[:8]}..."
    session_key_short.short_description = 'Session Key'
    
    def has_add_permission(self, request):
        # Prevent manual creation of sessions
        return False
