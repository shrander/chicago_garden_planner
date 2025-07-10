from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import UserProfile

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """
    Form for creating new users with case-insensitive validation
    and required email field
    """
    email = forms.EmailField(
        required=True,
        help_text="Required, Enter a valid email address."
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        help_text="Optional."
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        help_text="Optional."
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def clean_username(self):
        """Ensure username is unique (case-insensitive)"""
        username = self.cleaned_data.get("username")
        if username and User.objects.filter(username__iexact=username).exists():
            raise ValidationError(
                _("A user with that usename already exists"),
                code="duplicate_username",
            )
        return username.lower() # type: ignore
    
    def clean_email(self):
        """Ensure email is unique (case-insensitive)"""
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                _('A user with that email address already exists'),
                code='duplicate email',
            )
        return email.lower() # type: ignore

class CustomUserChangeForm(UserChangeForm):
    """Form for updating users with case-insensitive validation"""

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_username(self):
        """ensure username is unique (case-insensitive) when updating"""
        username = self.cleaned_data.get("username")
        if username and User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError(
                _("A user with that username already exists."),
                code='duplicate_username',
            )
        return username.lower() # type: ignore
    
    def clean_email(self):
        """Ensure email is unique (case-insensitive) when updating"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(
                _("A user with that email address already exists."),
                code='duplicate_email',
            )
        return email.lower() # type: ignore

class UserProfileForm(forms.ModelForm):
    """orm for updating user profile info"""

    class Meta:
        model = UserProfile
        fields = [
            'bio', 'location', 'gardening_zone', 'years_gardening',
            'organic_only', 'interests', 'email_notifications',
            'weekly_tips', 'avatar'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'interests': forms.Textarea(attrs={'rows': 3})
        }

class CaseInsensitiveAuthenticationForm(AuthenticationForm):
    """
    Override the default authenticationForm to provide better error messages
    and ensure case-insensitive login
    """
    username = forms.CharField(
        label=_("Username"),
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'placeholder': 'Enter your username'
        })
    )
    passowrd = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'placeholder': 'Enter your password'
        })
    )

    error_messages = {
        'Invalid_login': _(
            "Please enter a correct username and password. "
            "Note that password is case-sensitive"
        ),
        'inactive': _("This account is inactive"),
    }

class PasswordReseRequestForm(forms.Form):
    """Form for requesting password reset"""
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'Enter your email address'
        })
    )

    def clean_email(self):
        """Check if user with this email exists (case-insensitive)"""
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                _("No user is registered with this email address."),
                code='email_not_found',
            )
        return email.lower()