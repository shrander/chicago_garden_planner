# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chicago Garden Planner is a Django web application designed to help gardeners in the Chicago area (USDA zones 5b/6a) plan and manage their gardens with zone-specific plant recommendations, companion planting relationships, and interactive drag-and-drop garden design.

## Development Commands

### Environment Setup
```bash
# Create virtual environment (if not exists)
python3 -m venv garden_env

# Activate virtual environment
source garden_env/bin/activate  # Linux/macOS
garden_env\Scripts\activate     # Windows

# Install dependencies from requirements.txt
pip install -r requirements.txt
```

### Database Operations
```bash
# Create migrations
python manage.py makemigrations
python manage.py makemigrations gardens
python manage.py makemigrations accounts

# Apply migrations
python manage.py migrate

# Populate database with Chicago-specific plants
python manage.py populate_default_plants --create-sample-user

# Create companion plant relationships
python manage.py create_companion_relationships

# Create admin superuser
python manage.py createsuperuser
```

### Running the Application
```bash
# Start development server
python manage.py runserver

# Access points:
# - Main app: http://127.0.0.1:8000/
# - Admin: http://127.0.0.1:8000/admin/
# - Demo login: username=demo_gardener, password=chicago2025
```

### Testing
```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test accounts
python manage.py test gardens
```

### Static Files
```bash
# Collect static files for production
python manage.py collectstatic
```

### Database Management
```bash
# Backup data
python manage.py dumpdata gardens > garden_backup.json
python manage.py dumpdata accounts > accounts_backup.json

# Restore data
python manage.py loaddata garden_backup.json
```

## Architecture

### Custom User System

This project uses a **custom user model** (`accounts.CustomUser`) instead of Django's default User model. Key characteristics:

- **Case-insensitive username**: Usernames are stored in lowercase and lookups are case-insensitive via `CustomUserManager.get_by_natural_key()`
- **Required email field**: Email is unique and required for all users
- **ASCII-only usernames**: Uses `ASCIIUsernameValidator` for consistency
- **Auto-created profiles**: `UserProfile` is automatically created via signals when a user is created
- **Location**: `accounts.models.CustomUser`
- **Manager**: `accounts.managers.CustomUserManager`

**IMPORTANT**: The `AUTH_USER_MODEL = 'accounts.CustomUser'` setting must be set before the first migration. The accounts app must be listed in `INSTALLED_APPS` before `django.contrib.admin` to ensure the custom user model is registered properly.

### App Structure

#### accounts app
Handles user authentication, registration, and profile management.

- **Models**:
  - `CustomUser`: Custom user model extending AbstractBaseUser
  - `UserProfile`: Extended profile with gardening preferences, bio, location, USDA zone, avatar
- **Key Features**:
  - Case-insensitive login
  - User dashboard showing gardens and statistics
  - Profile editing (both account info and extended profile)
  - Password reset with email
  - Signal-based profile creation (see `accounts/signals.py`)
- **Views**: Class-based views for signup, login, profile editing; function-based for dashboard
- **Forms**: Custom forms in `accounts/forms.py` including `CaseInsensitiveAuthenticationForm`

#### gardens app
Core garden planning functionality.

- **Models** (implemented in `gardens/models.py`):
  - `Plant`: Plant library with Chicago-specific growing info, companion planting relationships, and pest deterrent information
    - Fields: name, latin_name, symbol, color, plant_type, planting_season, days_to_harvest, spacing_inches, chicago_notes
    - Many-to-many relationship with itself for companion plants
    - Can be user-created or system defaults (is_default flag)
  - `Garden`: User's garden layouts with grid-based design
    - Configurable sizes (4x4, 4x8, 8x8, 10x10, custom)
    - JSON-based layout storage for plant positions
    - Public/private sharing options
  - `PlantingNote`: Journal entries for specific plants in gardens with timestamps
- **Views**: Currently placeholder views (`gardens/views.py`) returning "coming soon" messages - need implementation
- **Management Commands**:
  - `populate_default_plants.py`: Loads 16+ default Chicago-optimized plants
  - `create_companion_relationships.py`: Sets up companion planting data

### URL Structure

- Root (`/`) redirects to `/gardens/`
- `/accounts/` - User authentication and profile management
- `/gardens/` - Garden list, creation, editing, and plant library
- `/admin/` - Django admin interface

### Settings Configuration

- **Time Zone**: `America/Chicago`
- **Static Files**: STATIC_ROOT = `BASE_DIR / 'staticfiles'`
- **Media Files**: MEDIA_ROOT = `BASE_DIR / 'media'` (for user avatars)
- **Email**: Console backend in development
- **Database**: SQLite3 (db.sqlite3)
- **Login redirects**:
  - LOGIN_URL = `'accounts:login'`
  - LOGIN_REDIRECT_URL = `'accounts:dashboard'`
  - LOGOUT_REDIRECT_URL = `'gardens:garden_list'`

## Development Workflow

### Adding New Features to gardens App

The gardens app currently has minimal implementation. When adding features:

1. Define models in `gardens/models.py` (Plant, Garden, etc.)
2. Create and run migrations
3. Update views in `gardens/views.py` (currently just placeholders)
4. Create templates in `gardens/templates/gardens/`
5. Add static files (CSS/JS) to `gardens/static/gardens/`

### Working with Custom User Model

When referencing the User model in code:

```python
from django.contrib.auth import get_user_model
User = get_user_model()
```

Do NOT import `django.contrib.auth.models.User` directly. Always use `get_user_model()` or reference `settings.AUTH_USER_MODEL` in foreign keys.

### Signal System

The accounts app uses Django signals (`accounts/signals.py`):
- Automatically creates `UserProfile` when a user is created
- Automatically saves profile when user is saved
- Deletes avatar files when profile is deleted

Ensure signals are connected by importing them in `accounts/apps.py`.

### Management Commands Location

Custom management commands go in:
- `gardens/management/commands/`
- Must include `__init__.py` files in both `management/` and `commands/` directories

## Chicago-Specific Features

This app is optimized for Chicago's climate (USDA zones 5b/6a):
- Frost date awareness
- Heat-tolerant plant varieties
- Seasonal planting calendars
- Humidity and pest management specific to the region
- Default plants include chicago_notes field with zone-specific guidance

## Dependencies

The project dependencies are defined in [requirements.txt](requirements.txt):

- **Django 4.2.7**: Web framework
- **Pillow**: Required for `ImageField` support (user avatars in UserProfile)
- **django-crispy-forms**: Form rendering with Bootstrap 5 styling
- **crispy-bootstrap5**: Bootstrap 5 template pack for crispy forms

When adding new dependencies, update requirements.txt and document any special configuration needed.

## Important Notes

- The project uses Django 4.2.7
- SECRET_KEY in settings.py is for development only - use environment variables in production
- Demo user credentials: `demo_gardener` / `chicago2025`
- Virtual environment should be in `garden_env/` directory
- The setup script (`setup_garden_project.py`) checks for virtual environment activation