from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import UserProfile

User = get_user_model()

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = (
        'bio', 'location', 'gardening_zone', 'years_gardening',
        'organics_only', 'interests', 'email_notifications', 'weekly_tips'
    )

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    inlines = [UserProfileInline]

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj) # type: ignore

# Register UserProfile separately for direct access
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'gardening_zone', 'years_gardening', 'organics_only']
    list_filter = ['gardening_zone', 'organics_only', 'email_notifications', 'weekly_tips']
    search_fields = ['user__username', 'user__email', 'location', 'interests']
    readonly_fields = ['user']
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Location & Experience', {
            'fields': ('location', 'gardening_zone', 'years_gardening', 'bio')
        }),
        ('Gardening Preferences', {
            'fields': ('organics_only', 'interests')
        }),
        ('Notifications', {
            'fields': ('email_notifications', 'weekly_tips')
        }),
        ('Profile Picture', {
            'fields': ('avatar',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent direct creation since profiles are auto-created via signals"""
        _ = request  # Intentionally unused - required by Django admin interface
        return False

