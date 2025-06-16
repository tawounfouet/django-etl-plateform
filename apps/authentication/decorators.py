from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse


def etl_permission_required(permission):
    """
    Decorator to check if user has specific ETL permission.
    
    Usage:
        @etl_permission_required('create_pipelines')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_etl_permission(permission):
                if request.is_ajax() or request.content_type == 'application/json':
                    return JsonResponse({
                        'error': f'Permission denied. Required permission: {permission}'
                    }, status=403)
                else:
                    messages.error(
                        request, 
                        f'You do not have permission to {permission.replace("_", " ")}.'
                    )
                    return redirect('ui:dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def staff_required(view_func):
    """
    Decorator to require staff status.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            if request.is_ajax() or request.content_type == 'application/json':
                return JsonResponse({
                    'error': 'Staff access required'
                }, status=403)
            else:
                messages.error(request, 'Staff access required.')
                return redirect('ui:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def superuser_required(view_func):
    """
    Decorator to require superuser status.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            if request.is_ajax() or request.content_type == 'application/json':
                return JsonResponse({
                    'error': 'Superuser access required'
                }, status=403)
            else:
                messages.error(request, 'Superuser access required.')
                return redirect('ui:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def multiple_etl_permissions_required(*permissions):
    """
    Decorator to check if user has multiple ETL permissions (AND logic).
    
    Usage:
        @multiple_etl_permissions_required('create_pipelines', 'modify_pipelines')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            for permission in permissions:
                if not request.user.has_etl_permission(permission):
                    missing_perms = [p.replace('_', ' ') for p in permissions]
                    if request.is_ajax() or request.content_type == 'application/json':
                        return JsonResponse({
                            'error': f'Permission denied. Required permissions: {", ".join(missing_perms)}'
                        }, status=403)
                    else:
                        messages.error(
                            request, 
                            f'You do not have the required permissions: {", ".join(missing_perms)}.'
                        )
                        return redirect('ui:dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def any_etl_permission_required(*permissions):
    """
    Decorator to check if user has any of the specified ETL permissions (OR logic).
    
    Usage:
        @any_etl_permission_required('create_pipelines', 'modify_pipelines')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            has_permission = any(
                request.user.has_etl_permission(permission) 
                for permission in permissions
            )
            
            if not has_permission:
                required_perms = [p.replace('_', ' ') for p in permissions]
                if request.is_ajax() or request.content_type == 'application/json':
                    return JsonResponse({
                        'error': f'Permission denied. At least one required: {", ".join(required_perms)}'
                    }, status=403)
                else:
                    messages.error(
                        request, 
                        f'You need at least one of these permissions: {", ".join(required_perms)}.'
                    )
                    return redirect('ui:dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def api_key_required(view_func):
    """
    Decorator for API views that require API key authentication.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        api_key = request.META.get('HTTP_X_API_KEY')
        
        if not api_key:
            return JsonResponse({
                'error': 'API key required'
            }, status=401)
        
        # Here you would validate the API key against your API key model
        # For now, this is a placeholder
        if api_key != 'your-secret-api-key':
            return JsonResponse({
                'error': 'Invalid API key'
            }, status=401)
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


class ETLPermissionMixin:
    """
    Mixin for class-based views to check ETL permissions.
    """
    required_etl_permission = None
    required_etl_permissions = None  # For multiple permissions (AND logic)
    any_etl_permissions = None  # For multiple permissions (OR logic)
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('authentication:login')
        
        # Check single permission
        if self.required_etl_permission:
            if not request.user.has_etl_permission(self.required_etl_permission):
                messages.error(
                    request, 
                    f'You do not have permission to {self.required_etl_permission.replace("_", " ")}.'
                )
                return redirect('ui:dashboard')
        
        # Check multiple permissions (AND logic)
        if self.required_etl_permissions:
            for permission in self.required_etl_permissions:
                if not request.user.has_etl_permission(permission):
                    missing_perms = [p.replace('_', ' ') for p in self.required_etl_permissions]
                    messages.error(
                        request, 
                        f'You do not have the required permissions: {", ".join(missing_perms)}.'
                    )
                    return redirect('ui:dashboard')
        
        # Check multiple permissions (OR logic)
        if self.any_etl_permissions:
            has_permission = any(
                request.user.has_etl_permission(permission) 
                for permission in self.any_etl_permissions
            )
            if not has_permission:
                required_perms = [p.replace('_', ' ') for p in self.any_etl_permissions]
                messages.error(
                    request, 
                    f'You need at least one of these permissions: {", ".join(required_perms)}.'
                )
                return redirect('ui:dashboard')
        
        return super().dispatch(request, *args, **kwargs)
