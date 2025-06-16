from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import UserProfile, UserSession
from .forms import CustomUserCreationForm, CustomAuthenticationForm

User = get_user_model()


class CustomUserModelTest(TestCase):
    """
    Test cases for the CustomUser model.
    """
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }
    
    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password('testpass123'))
    
    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(**self.user_data)
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        # Check ETL permissions
        self.assertTrue(user.can_create_pipelines)
        self.assertTrue(user.can_modify_pipelines)
        self.assertTrue(user.can_execute_pipelines)
        self.assertTrue(user.can_view_monitoring)
        self.assertTrue(user.can_manage_connectors)
    
    def test_user_string_representation(self):
        """Test the string representation of user."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')
    
    def test_get_full_name(self):
        """Test get_full_name method."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), 'Test User')
    
    def test_get_short_name(self):
        """Test get_short_name method."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_short_name(), 'Test')
    
    def test_has_etl_permission(self):
        """Test ETL permission checking."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            can_create_pipelines=True,
            can_execute_pipelines=False
        )
        
        self.assertTrue(user.has_etl_permission('create_pipelines'))
        self.assertFalse(user.has_etl_permission('execute_pipelines'))
        self.assertFalse(user.has_etl_permission('nonexistent_permission'))
    
    def test_email_unique_constraint(self):
        """Test that email must be unique."""
        User.objects.create_user(**self.user_data)
        
        with self.assertRaises(Exception):  # IntegrityError
            User.objects.create_user(**self.user_data)


class UserProfileModelTest(TestCase):
    """
    Test cases for the UserProfile model.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_create_user_profile(self):
        """Test creating a user profile."""
        profile = UserProfile.objects.create(
            user=self.user,
            timezone='America/New_York',
            language='en',
            bio='Test bio'
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.timezone, 'America/New_York')
        self.assertEqual(profile.language, 'en')
        self.assertEqual(profile.bio, 'Test bio')
        self.assertTrue(profile.email_notifications)
        self.assertTrue(profile.pipeline_notifications)
    
    def test_profile_string_representation(self):
        """Test the string representation of profile."""
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(str(profile), 'test@example.com Profile')


class AuthenticationFormsTest(TestCase):
    """
    Test cases for authentication forms.
    """
    
    def test_custom_user_creation_form_valid(self):
        """Test valid user creation form."""
        form_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_custom_user_creation_form_invalid_email(self):
        """Test user creation form with invalid email."""
        form_data = {
            'email': 'invalid-email',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_custom_authentication_form_valid(self):
        """Test valid authentication form."""
        # Create a user first
        User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        form_data = {
            'username': 'test@example.com',  # Note: username field for email
            'password': 'testpass123',
        }
        form = CustomAuthenticationForm(data=form_data)
        self.assertTrue(form.is_valid())


class AuthenticationViewsTest(TestCase):
    """
    Test cases for authentication views.
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_login_view_get(self):
        """Test GET request to login view."""
        response = self.client.get(reverse('authentication:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
    
    def test_login_view_post_valid(self):
        """Test POST request to login view with valid credentials."""
        response = self.client.post(reverse('authentication:login'), {
            'username': 'test@example.com',
            'password': 'testpass123',
        })
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
    
    def test_login_view_post_invalid(self):
        """Test POST request to login view with invalid credentials."""
        response = self.client.post(reverse('authentication:login'), {
            'username': 'test@example.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password')
    
    def test_logout_view(self):
        """Test logout view."""
        # Login first
        self.client.login(username='test@example.com', password='testpass123')
        
        response = self.client.get(reverse('authentication:logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout
    
    def test_register_view_get(self):
        """Test GET request to register view."""
        response = self.client.get(reverse('authentication:register'))
        self.assertEqual(response.status_code, 200)
    
    def test_register_view_post_valid(self):
        """Test POST request to register view with valid data."""
        response = self.client.post(reverse('authentication:register'), {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'newpass123!',
            'password2': 'newpass123!',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        
        # Check if user was created
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
    
    def test_profile_view_requires_login(self):
        """Test that profile view requires authentication."""
        response = self.client.get(reverse('authentication:profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_profile_view_authenticated(self):
        """Test profile view for authenticated user."""
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('authentication:profile'))
        self.assertEqual(response.status_code, 200)


class UserSessionModelTest(TestCase):
    """
    Test cases for the UserSession model.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_create_user_session(self):
        """Test creating a user session."""
        session = UserSession.objects.create(
            user=self.user,
            session_key='test_session_key',
            ip_address='127.0.0.1',
            user_agent='Test User Agent'
        )
        
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.session_key, 'test_session_key')
        self.assertEqual(session.ip_address, '127.0.0.1')
        self.assertTrue(session.is_active)
    
    def test_session_string_representation(self):
        """Test the string representation of session."""
        session = UserSession.objects.create(
            user=self.user,
            session_key='test_session_key',
            ip_address='127.0.0.1',
            user_agent='Test User Agent'
        )
        expected = f"{self.user.email} - test_ses..."
        self.assertEqual(str(session), expected)
