from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager

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
    location = models.CharField(max_length=150, blank=True, help_text='City, State')
    HARDINESS_ZONES = [
        ('3a', 'Zone 3a (-40°F to -35°F)'),
        ('3b', 'Zone 3b (-35°F to -30°F)'),
        ('4a', 'Zone 4a (-30°F to -25°F)'),
        ('4b', 'Zone 4b (-25°F to -20°F)'),
        ('5a', 'Zone 5a (-20°F to -15°F)'),
        ('5b', 'Zone 5b (-15°F to -10°F)'),
        ('6a', 'Zone 6a (-10°F to -5°F)'),
        ('6b', 'Zone 6b (-5°F to 0°F)'),
        ('7a', 'Zone 7a (0°F to 5°F)'),
        ('7b', 'Zone 7b (5°F to 10°F)'),
        ('8a', 'Zone 8a (10°F to 15°F)'),
        ('8b', 'Zone 8b (15°F to 20°F)'),
        ('9a', 'Zone 9a (20°F to 25°F)'),
        ('9b', 'Zone 9b (25°F to 30°F)'),
        ('10a', 'Zone 10a (30°F to 35°F)'),
        ('10b', 'Zone 10b (35°F to 40°F)'),
    ]

    gardening_zone = models.CharField(
        max_length=10,
        blank=True,
        default='5b',
        choices=HARDINESS_ZONES,
        help_text='USDA Hardiness Zone (Chicago is typically 5b/6a)'
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

    # Email
    email_notifications = models.BooleanField(
        default=True,
        help_text='Receive email notifications about planting reminders'
    )
    weekly_tips = models.BooleanField(
        default=True,
        help_text='Receive weekly gardening tips'
    )

    # avatar
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text='Profile Picture'
    )

    class Meta: 
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"{self.user.username}'s profile"