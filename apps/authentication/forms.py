from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserProfile


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user creation form for registration.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Department (optional)'
        })
    )
    
    job_title = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Job title (optional)'
        })
    )

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'first_name',
            'last_name',
            'department',
            'job_title',
            'password1',
            'password2'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """
    Custom user change form for admin interface.
    """
    
    class Meta:
        model = CustomUser
        fields = (
            'email',
            'first_name',
            'last_name',
            'department',
            'job_title',
            'phone',
            'is_active',
            'is_staff'
        )


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form using email instead of username.
    """
    username = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        # Remove the username field help text
        self.fields['username'].help_text = None

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class UserProfileForm(forms.ModelForm):
    """
    Form for editing user profile information.
    """
    
    class Meta:
        model = UserProfile
        fields = [
            'avatar',
            'bio',
            'timezone',
            'language',
            'email_notifications',
            'pipeline_notifications'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'timezone': forms.Select(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pipeline_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PasswordChangeForm(forms.Form):
    """
    Custom password change form.
    """
    old_password = forms.CharField(
        label=_('Current password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        })
    )
    
    new_password1 = forms.CharField(
        label=_('New password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )
    
    new_password2 = forms.CharField(
        label=_('Confirm new password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError(_('Your old password was entered incorrectly.'))
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError(_('The two password fields didn\'t match.'))
        
        return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user
