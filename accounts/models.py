from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager
from .encryption import encrypt_value, decrypt_value
from gardens.constants import HARDINESS_ZONES

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with case-insensitive username and email
    Username only accepts ASCII characters for consistency
    email is required and must be unique
    """
    username_validator = ASCIIUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_("Required. 150 characters or fewer. Letters, numbers, and @/./+/-/_ only"),
        validators=[username_validator],
        error_messages={
            "unique": _("That username already exists"),
        },
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique', _("Email address exists already")
        }, # type: ignore
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether user can log into the admin panel")
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should treated as active"
            "Unselect this instead of deleting accounts"
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = CustomUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta: 
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email) # type: ignore
        #store username as lowercase
        self.username = self.username.lower()

    def get_full_name(self):
        """Return the first_name plus the last_name"""
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()
    
    def get_short_name(self):
        """Return short/first name"""
        return self.first_name
    
    def email_user(self, subject, message, from_email=None, **kwargs):
        """send an email to this user"""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def __str__(self):
        return self.username
    
class UserProfile(models.Model):
    """
    Extended profile for users to store gardening preferences and info.
    Created automatically when a user is creatd via signals.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio=models.TextField(max_length=500, blank=True, help_text='Tell us about your gardening experience')
    location = models.CharField(max_length=150, blank=True, help_text='City, State (deprecated - use location_name instead)')

    # Location and zone information
    location_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='City and state (e.g., "Chicago, IL")'
    )

    gardening_zone = models.CharField(
        max_length=3,
        blank=True,
        default='5b',
        choices=HARDINESS_ZONES,
        help_text='USDA Hardiness Zone'
    )

    # Custom frost dates override
    custom_frost_dates = models.JSONField(
        default=dict,
        blank=True,
        help_text='Custom last/first frost dates: {"last_frost": "MM-DD", "first_frost": "MM-DD"}'
    )
    year_started_gardening = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='What year did you start gardening?'
    )

    @property
    def years_gardening(self):
        """Calculate years gardening from year_started_gardening"""
        if self.year_started_gardening:
            from django.utils import timezone
            current_year = timezone.now().year
            return current_year - self.year_started_gardening
        return None

    # Gardening preferences
    organics_only = models.BooleanField(default=False, help_text='Interested only in organic gardening methods')
    interests = models.TextField(
        blank=True,
        help_text='What are you most interested in growing?'
    )

    # Email and notifications
    email_notifications = models.BooleanField(
        default=True,
        help_text='Receive daily email notifications about planting and harvest reminders'
    )
    weekly_tips = models.BooleanField(
        default=True,
        help_text='Receive weekly gardening digest and tips'
    )
    notification_timezone = models.CharField(
        max_length=50,
        default='America/Chicago',
        help_text='Your local timezone for scheduling notifications (e.g., America/New_York, America/Los_Angeles)'
    )

    # avatar
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text='Profile Picture'
    )

    # AI Assistant API Key (encrypted in database)
    _anthropic_api_key_encrypted = models.TextField(
        blank=True,
        db_column='anthropic_api_key',
        help_text='Encrypted Anthropic API key for AI Garden Assistant features'
    )

    @property
    def anthropic_api_key(self):
        """Decrypt and return the API key"""
        if not self._anthropic_api_key_encrypted:
            return ''
        try:
            return decrypt_value(self._anthropic_api_key_encrypted)
        except Exception:
            # If decryption fails, return empty string
            return ''

    @anthropic_api_key.setter
    def anthropic_api_key(self, value):
        """Encrypt and store the API key"""
        if value:
            self._anthropic_api_key_encrypted = encrypt_value(value)
        else:
            self._anthropic_api_key_encrypted = ''

    def get_climate_zone(self):
        """Get ClimateZone instance for user's gardening zone"""
        from gardens.models import ClimateZone
        if self.gardening_zone:
            try:
                return ClimateZone.objects.get(zone=self.gardening_zone)
            except ClimateZone.DoesNotExist:
                pass
        return None

    def get_frost_dates(self):
        """Get frost dates for this user (custom or zone defaults)"""
        from datetime import datetime
        from gardens.utils import parse_frost_date, get_default_zone

        # Check for custom frost dates first
        if self.custom_frost_dates and self.custom_frost_dates.get('last_frost'):
            current_year = datetime.now().year
            try:
                return {
                    'last_frost': parse_frost_date(current_year, self.custom_frost_dates['last_frost']),
                    'first_frost': parse_frost_date(current_year, self.custom_frost_dates['first_frost']),
                }
            except (ValueError, KeyError):
                pass

        # Use zone defaults
        climate = self.get_climate_zone()
        if climate:
            current_year = datetime.now().year
            try:
                return {
                    'last_frost': parse_frost_date(current_year, climate.typical_last_frost),
                    'first_frost': parse_frost_date(current_year, climate.typical_first_frost),
                }
            except ValueError:
                pass

        # Fallback to default zone from settings
        current_year = datetime.now().year
        default_zone = get_default_zone()

        try:
            from gardens.models import ClimateZone
            climate = ClimateZone.objects.get(zone=default_zone)
            return {
                'last_frost': parse_frost_date(current_year, climate.typical_last_frost),
                'first_frost': parse_frost_date(current_year, climate.typical_first_frost),
            }
        except:
            # Final fallback to hardcoded dates (Chicago 5b)
            return {
                'last_frost': parse_frost_date(current_year, "05-15"),
                'first_frost': parse_frost_date(current_year, "10-15"),
            }

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"{self.user.username}'s profile"