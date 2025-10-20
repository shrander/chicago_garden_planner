# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chicago Garden Planner is a Django-based web application for planning and managing gardens with Chicago-specific growing advice (USDA zones 5b/6a). The app features:

- Custom user authentication with case-insensitive username lookup
- User profiles with gardening preferences and avatar support
- Garden planning interface (intended for drag-and-drop functionality)
- Plant library with Chicago-optimized default plants and companion planting relationships
- User dashboard for managing multiple gardens

## Development Commands

### Initial Setup
```bash
# Activate virtual environment
source garden_env/bin/activate  # macOS/Linux
garden_env\Scripts\activate     # Windows

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Populate database with Chicago plants and demo data
python manage.py populate_default_plants --create-sample-user

# Create companion plant relationships
python manage.py create_companion_relationships

# Create admin superuser
python manage.py createsuperuser
```

### Daily Development
```bash
# Start development server
python manage.py runserver

# Run Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic
```

### Database Operations
```bash
# Create new migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Backup data
python manage.py dumpdata gardens > garden_backup.json
python manage.py loaddata garden_backup.json

# Reset database (development only)
rm db.sqlite3
rm gardens/migrations/0*.py accounts/migrations/0*.py
python manage.py makemigrations
python manage.py migrate
python manage.py populate_default_plants --create-sample-user
```

### Testing
```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test accounts
python manage.py test gardens

# Run specific test class or method
python manage.py test accounts.tests.TestClassName
python manage.py test accounts.tests.TestClassName.test_method_name
```

## Architecture

### Custom User System

The project uses a **custom user model** (`accounts.CustomUser`) instead of Django's default User model. This is critical to understand:

- **Custom user model**: `accounts.CustomUser` (set via `AUTH_USER_MODEL = 'accounts.CustomUser'`)
- **Case-insensitive authentication**: Usernames are stored lowercase and lookups are case-insensitive via `CustomUserManager.get_by_natural_key()`
- **Required fields**: Both username and email are required; email must be unique
- **User profiles**: A `UserProfile` is automatically created for each user via Django signals ([accounts/signals.py:8-25](accounts/signals.py#L8-L25))

**Important**: The custom user model MUST be set before the first migration. If you need to change user-related models:
1. Always import the user model with `get_user_model()`, never import `User` directly
2. Use `settings.AUTH_USER_MODEL` for ForeignKey references in models
3. The accounts app must be listed BEFORE `django.contrib.admin` in `INSTALLED_APPS` ([garden_planner/settings.py:40](garden_planner/settings.py#L40))

### Django Apps Structure

**accounts/** - User authentication and profile management
- Custom user model with case-insensitive username lookup
- User profiles with gardening preferences (zone, experience, notifications)
- Signal-based profile creation (automatic on user creation)
- Custom authentication form for case-insensitive login

**gardens/** - Core garden planning functionality
- Plant library (models not yet implemented in models.py)
- Garden management (models referenced but not yet implemented)
- Management commands for seeding Chicago-specific plant data
- Placeholder views (implementation in progress)

**garden_planner/** - Django project configuration
- Settings configured for Chicago timezone (`America/Chicago`)
- Email backend set to console for development
- Custom login redirects to user dashboard
- Static/media file configuration

### Key Patterns

**Signals for Profile Management**: User profiles are created automatically via Django signals rather than form logic. See [accounts/signals.py](accounts/signals.py) - this ensures every user has a profile regardless of how the user is created.

**Case-Insensitive Username**: The `CustomUserManager` overrides `get_by_natural_key()` to perform case-insensitive username lookups ([accounts/managers.py:46-51](accounts/managers.py#L46-L51)). Usernames are normalized to lowercase on save ([accounts/models.py:66](accounts/models.py#L66)).

**Management Commands**: The project uses custom Django management commands for data seeding:
- `populate_default_plants.py`: Seeds Chicago-optimized plants with growing information
- `create_companion_relationship.py`: Creates companion planting relationships

These should be extended (not replaced) when adding new default data.

### Project State Notes

- **gardens/models.py** is currently minimal - the Plant, Garden, and PlantingNote models referenced in views and commands are not yet implemented
- **gardens/views.py** contains only placeholder views returning HTTP responses
- Templates directory exists but is empty ([gardens/templates/gardens/](gardens/templates/gardens/))
- The README indicates this project was set up from artifacts, suggesting it may be in mid-migration or setup phase

### URL Structure

- Root `/` redirects to `/gardens/`
- `/accounts/` - User authentication and profile management
- `/gardens/` - Garden planning and plant library
- `/admin/` - Django admin interface

### Settings Configuration

- **Timezone**: `America/Chicago` - important for planting season calculations
- **Database**: SQLite (development), should use PostgreSQL for production
- **Static files**: Collected to `staticfiles/` directory
- **Media files**: User uploads go to `media/` directory
- **Email**: Console backend for development (prints to terminal)
- **Debug mode**: Currently enabled (`DEBUG = True`)

## Demo Credentials

```
Username: demo_gardener
Password: chicago2025
```
