"""Context processors for adding data to templates"""
from .admin_views import get_system_stats


def admin_stats(request):
    """Add system stats to admin templates"""
    # Only add stats for admin pages and staff users
    if request.path.startswith('/admin/') and request.user.is_staff:
        try:
            return get_system_stats()
        except Exception:
            return {}
    return {}
