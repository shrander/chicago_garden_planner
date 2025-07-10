from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile when a new user is created
    """
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile whenever the user is saved.
    Create profile if it doesn't exist (for existing users)
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)

@receiver(pre_delete, sender=UserProfile)
def delete_user_avatar(sender, instance, **kwargs):
    """
    Delete the avatar file when a UserProfile is deleted
    """
    if instance.avatar:
        instance.avatar.delete(save=False)