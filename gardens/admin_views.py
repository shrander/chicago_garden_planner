"""Custom admin views for system statistics"""
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import psutil
import platform

User = get_user_model()


@staff_member_required
def get_system_stats():
    """Get system statistics for admin dashboard"""
    # Get active users (sessions active in last 15 minutes)
    from django.contrib.sessions.models import Session

    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())  # type: ignore[attr-defined]
    active_user_ids = []

    for session in active_sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')
        if user_id:
            active_user_ids.append(int(user_id))

    active_users = User.objects.filter(id__in=active_user_ids)  # type: ignore[attr-defined]

    # Get system statistics
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        system_stats = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024 ** 3),
            'memory_total_gb': memory.total / (1024 ** 3),
            'disk_percent': disk.percent,
            'disk_used_gb': disk.used / (1024 ** 3),
            'disk_total_gb': disk.total / (1024 ** 3),
            'platform': platform.system(),
            'platform_release': platform.release(),
            'python_version': platform.python_version(),
        }
    except Exception as e:
        system_stats = {'error': str(e)}

    # Get user statistics
    total_users = User.objects.count()  # type: ignore[attr-defined]
    staff_users = User.objects.filter(is_staff=True).count()  # type: ignore[attr-defined]
    superusers = User.objects.filter(is_superuser=True).count()  # type: ignore[attr-defined]

    # Get app statistics
    from gardens.models import Garden, Plant, PlantInstance

    total_gardens = Garden.objects.count()  # type: ignore[attr-defined]
    total_plants = Plant.objects.count()  # type: ignore[attr-defined]
    total_plant_instances = PlantInstance.objects.count()  # type: ignore[attr-defined]
    default_plants = Plant.objects.filter(is_default=True).count()  # type: ignore[attr-defined]
    custom_plants = Plant.objects.filter(is_default=False).count()  # type: ignore[attr-defined]

    return {
        'active_users': active_users,
        'active_user_count': len(active_user_ids),
        'system_stats': system_stats,
        'user_stats': {
            'total': total_users,
            'staff': staff_users,
            'superusers': superusers,
        },
        'app_stats': {
            'total_gardens': total_gardens,
            'total_plants': total_plants,
            'total_plant_instances': total_plant_instances,
            'default_plants': default_plants,
            'custom_plants': custom_plants,
        }
    }
