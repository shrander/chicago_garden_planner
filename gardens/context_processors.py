"""Context processors for adding data to templates"""
from .admin_views import get_system_stats
import logging

logger = logging.getLogger(__name__)


def admin_stats(request):
    """Add system stats to admin templates"""
    # Only add stats for admin pages and authenticated staff users
    if not request.path.startswith('/admin/'):
        return {}

    if not request.user.is_authenticated:
        return {}

    if not request.user.is_staff:
        return {}

    try:
        stats = get_system_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}", exc_info=True)
        return {
            'stats_error': str(e)
        }
