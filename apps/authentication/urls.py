from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Profile management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Session management
    path('sessions/', views.user_sessions, name='sessions'),
    path('sessions/revoke/<int:session_id>/', views.revoke_session, name='revoke_session'),
    
    # API endpoints
    path('api/login/', views.api_login, name='api_login'),
]
