"""
Context processors for making global variables available in all templates
"""
import subprocess
from pathlib import Path
from django.conf import settings


def version(request):
    """
    Add application version to template context

    Tries to get version in this order:
    1. Git tag (e.g., 'v1.0.0' or '1.0.0') - used in production
    2. Git commit SHA (short) - used in development
    3. VERSION file fallback
    4. 'dev' if nothing else works
    """
    try:
        # Try to get the current git tag
        result = subprocess.run(
            ['git', 'describe', '--tags', '--exact-match'],
            cwd=settings.BASE_DIR,
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            tag = result.stdout.strip()
            # Remove 'v' prefix if present (v1.0.0 -> 1.0.0)
            app_version = tag[1:] if tag.startswith('v') else tag
            return {'APP_VERSION': app_version}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    try:
        # If not on a tag, get the short commit SHA for development
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=settings.BASE_DIR,
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            commit = result.stdout.strip()
            app_version = f'dev-{commit}'
            return {'APP_VERSION': app_version}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback to VERSION file
    version_file = Path(settings.BASE_DIR) / 'VERSION'
    try:
        app_version = version_file.read_text().strip()
    except FileNotFoundError:
        app_version = 'dev'

    return {
        'APP_VERSION': app_version
    }
