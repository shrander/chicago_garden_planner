# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chicago Garden Planner is a Django web application designed to help gardeners across North America plan and manage their gardens with zone-specific plant recommendations, companion planting relationships, and interactive drag-and-drop garden design. Originally created for Chicago (USDA zones 5b/6a), now expanded to support all 16 USDA hardiness zones (3a-10b).

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

# Populate database with default plants
python manage.py populate_default_plants --create-sample-user

# Populate climate zone data (all 16 USDA zones)
python manage.py populate_climate_zones

# Populate plant zone success ratings
python manage.py populate_plant_zone_ratings

# Create companion plant relationships
python manage.py create_companion_relationship

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
  - `Plant`: Plant library with zone-specific growing info, companion planting relationships, and pest deterrent information
    - Fields: name, latin_name, symbol, color, plant_type, planting_season, days_to_harvest, spacing_inches, growing_notes
  - `ClimateZone`: Climate and growing information for USDA hardiness zones
    - Frost dates, growing season days, temperature ranges, soil types, special considerations
  - `PlantZoneData`: Zone-specific success ratings and growing notes for plants
    - Success rating (1-5 stars), zone_specific_notes, soil_amendments, special_considerations
    - Many-to-many relationship with itself for companion plants
    - Can be user-created or system defaults (is_default flag)
  - `Garden`: User's garden layouts with grid-based design
    - Configurable sizes (4x4, 4x8, 8x8, 10x10, custom)
    - JSON-based layout storage for plant positions
    - Public/private sharing options
  - `PlantingNote`: Journal entries for specific plants in gardens with timestamps
- **Views**: Currently placeholder views (`gardens/views.py`) returning "coming soon" messages - need implementation
- **Management Commands**:
  - `populate_default_plants.py`: Loads 20+ default plants with growing information
  - `populate_climate_zones.py`: Loads all 16 USDA hardiness zones with climate data
  - `populate_plant_zone_ratings.py`: Loads zone-specific success ratings for common plants
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

## Code Organization & Maintainability Guidelines

### DRY Principle & File Size Limits

**IMPORTANT**: To maintain code quality and prevent technical debt:

#### Template File Limits
- **Maximum template size**: 500 lines
- **If exceeding 500 lines**: Extract partials to `templates/{app}/partials/`
- **No embedded JavaScript >50 lines**: Extract to static JS files
- **No embedded CSS >50 lines**: Extract to static CSS files

#### JavaScript Organization
All JavaScript must be in external files:

```
gardens/static/gardens/js/
├── utils.js           # Reusable utilities (CSRF, fetch, ButtonStateManager)
├── api.js             # API client classes (future)
├── {feature}.js       # Feature-specific code
└── garden-detail.js   # Page-specific logic
```

**Required utilities** (already created in `utils.js`):
- `getCSRFToken()` - Get CSRF token for AJAX
- `gardenFetch(url, options)` - Wrapper for fetch with Django defaults
- `ButtonStateManager` class - Manage button loading/success/error states
- `showModal(modalId)` / `hideModal(modalId)` - Modal helpers

**Usage example**:
```javascript
// GOOD: Use utilities
const api = gardenFetch('/gardens/1/clear/', { method: 'POST' });

// BAD: Duplicate fetch code
fetch('/gardens/1/clear/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()}
})
```

#### CSS Organization
All CSS must be in external files:

```
gardens/static/gardens/css/
├── base.css           # Global styles
├── garden-detail.css  # Page-specific styles
└── {feature}.css      # Feature-specific styles
```

#### Template Partials
Extract repeated UI patterns:

```
gardens/templates/gardens/partials/
├── _modals/
│   ├── _ai_assistant.html
│   ├── _clear_confirm.html
│   └── _delete_confirm.html
├── _garden_grid.html
└── _plant_library.html
```

**Usage**:
```django
{% include 'gardens/partials/_modals/_ai_assistant.html' %}
{% include 'gardens/partials/_garden_grid.html' with grid=grid_data %}
```

#### Django View Guidelines

**Use mixins for repeated patterns**:
```python
# gardens/mixins.py (create this file)
class JSONResponseMixin:
    def json_success(self, data=None, message=None):
        return JsonResponse({'success': True, 'message': message, **data})

    def json_error(self, error, status=400):
        return JsonResponse({'success': False, 'error': str(error)}, status=status)

# Usage in views
class GardenClearView(JSONResponseMixin, View):
    def post(self, request, pk):
        try:
            # ... logic ...
            return self.json_success(message='Cleared')
        except Exception as e:
            return self.json_error(e, status=500)
```

**Avoid duplicating**:
- Error handling logic
- JSON response formatting
- Permission checking
- Get object or 404 patterns

### Code Review Checklist

Before committing, check:

- [ ] No template file >500 lines
- [ ] No embedded JS >50 lines (extract to static file)
- [ ] No embedded CSS >50 lines (extract to static file)
- [ ] No duplicate fetch() patterns (use `gardenFetch()`)
- [ ] No duplicate button state management (use `ButtonStateManager`)
- [ ] No duplicate JSON responses (use mixins)
- [ ] Modal logic uses `showModal()`/`hideModal()`
- [ ] CSRF always via `getCSRFToken()`, never duplicated

### Development Workflow

#### Adding New Features to gardens App

When adding features:

1. **Models**: Define in `gardens/models.py`
2. **Migrations**: Create and run migrations
3. **Views**: Add to `gardens/views.py` (use mixins for common patterns)
4. **Templates**: Create in `gardens/templates/gardens/`
   - Keep main template <500 lines
   - Extract partials if needed
5. **Static Files**:
   - JavaScript → `gardens/static/gardens/js/{feature}.js`
   - CSS → `gardens/static/gardens/css/{feature}.css`
   - Use existing utilities from `utils.js`

#### Adding JavaScript Features

1. **Check if utility exists**: Look in `utils.js` first
2. **Reusable code**: Add to `utils.js`
3. **Feature-specific**: Create new `{feature}.js` file
4. **Load order**: Load `utils.js` before feature files

```django
<!-- In template -->
<script src="{% static 'gardens/js/utils.js' %}"></script>
<script src="{% static 'gardens/js/my-feature.js' %}"></script>
```

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

## Multi-Zone Support

The app supports all 16 USDA hardiness zones (3a-10b):
- **Automatic climate adaptation**: Frost dates, growing season info for user's zone
- **Zone-specific plant ratings**: Success ratings (1-5 stars) for each plant by zone
- **Tailored growing advice**: Zone-specific notes, soil amendments, special considerations
- **AI zone-awareness**: AI assistant provides zone-appropriate recommendations
- **Custom frost dates**: Users can override defaults with microclimate data
- **Default zone**: Chicago (5b) for backward compatibility and anonymous users

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