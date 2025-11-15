from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in with either
    their username or email address (both case-insensitive).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user with username or email (case-insensitive)

        Args:
            request: The HTTP request
            username: Can be either username or email
            password: The password to verify
            **kwargs: Additional keyword arguments

        Returns:
            User object if authentication successful, None otherwise
        """
        if username is None or password is None:
            return None

        try:
            # Try to find user by username or email (case-insensitive)
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # If multiple users found (shouldn't happen with unique constraints),
            # try username first, then email
            user = User.objects.filter(username__iexact=username).first()
            if not user:
                user = User.objects.filter(email__iexact=username).first()
            if not user:
                return None

        # Check password and user.is_active
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
