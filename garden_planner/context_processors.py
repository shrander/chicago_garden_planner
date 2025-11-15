"""
Context processors for making global variables available in all templates
"""
from pathlib import Path
from django.conf import settings


def version(request):
    """
    Add application version to template context
    Reads version from VERSION file in project root
    """
    version_file = Path(settings.BASE_DIR) / 'VERSION'
    try:
        app_version = version_file.read_text().strip()
    except FileNotFoundError:
        app_version = 'dev'

    return {
        'APP_VERSION': app_version
    }
