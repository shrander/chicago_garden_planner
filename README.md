# 🌱 Chicago Garden Planner

A Django web application designed to help gardeners in the Chicago area (USDA zones 5b/6a) plan and manage their gardens with zone-specific plant recommendations, companion planting relationships, and interactive drag-and-drop garden design.

## Features

- ✅ **Interactive Garden Designer**: Drag-and-drop interface for planning garden layouts
- ✅ **Chicago-Specific Plant Library**: 20+ plants optimized for zones 5b/6a with local growing tips
- ✅ **Companion Planting**: Smart recommendations for plant combinations
- ✅ **AI Garden Assistant**: Get AI-powered layout suggestions based on your preferences
- ✅ **Yield Calculations**: Automatic calculation of expected harvest yields
- ✅ **Garden Sharing**: Share your garden designs with friends via email invitations
- ✅ **Access Control**: Manage who can view and edit your gardens
- ✅ **Responsive Design**: Works on desktop, tablet, and mobile devices

## Quick Start - Development

### Prerequisites

- Python 3.8 or higher
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/chicago_garden_planner.git
cd chicago_garden_planner
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv garden_env

# Activate virtual environment
source garden_env/bin/activate  # On macOS/Linux
garden_env\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Database

```bash
# Run migrations
python manage.py migrate

# Populate with Chicago-specific plants and create demo user
python manage.py populate_default_plants --create-sample-user

# (Optional) Create your own admin account
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

The application will be available at:
- **Main app**: http://127.0.0.1:8000/
- **Admin panel**: http://127.0.0.1:8000/admin/

### 6. Login with Demo Account

- **Username**: `demo_gardener`
- **Password**: `chicago2025`

## Development Workflow

### Starting the Development Server

```bash
# Navigate to project directory
cd chicago_garden_planner

# Activate virtual environment
source garden_env/bin/activate  # macOS/Linux
garden_env\Scripts\activate     # Windows

# Start server
python manage.py runserver

# Or run on different port
python manage.py runserver 8080

# Or make accessible from other devices on your network
python manage.py runserver 0.0.0.0:8000
```

### Common Development Commands

```bash
# Run tests
python manage.py test

# Create database migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Access Django shell
python manage.py shell

# Collect static files (for production)
python manage.py collectstatic

# Create superuser
python manage.py createsuperuser

# Load default plants
python manage.py populate_default_plants

# Backup database
python manage.py dumpdata gardens > garden_backup.json
python manage.py dumpdata accounts > accounts_backup.json

# Restore database
python manage.py loaddata garden_backup.json
```

## Project Structure

```
chicago_garden_planner/
├── garden_env/                 # Virtual environment
├── db.sqlite3                  # SQLite database (development)
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── garden_planner/             # Main Django project
│   ├── settings.py            # Django settings
│   ├── settings_production.py # Production settings
│   ├── urls.py                # Main URL configuration
│   └── wsgi.py                # WSGI configuration
├── accounts/                   # User management app
│   ├── models.py              # CustomUser, UserProfile
│   ├── views.py               # Auth views
│   ├── forms.py               # User forms
│   └── templates/             # User templates
├── gardens/                    # Garden planning app
│   ├── models.py              # Plant, Garden, PlantingNote
│   ├── views.py               # Garden views and API endpoints
│   ├── forms.py               # Garden forms
│   ├── templatetags/          # Custom template filters
│   ├── management/commands/   # Custom management commands
│   ├── templates/gardens/     # HTML templates
│   └── static/gardens/        # CSS, JavaScript
├── scripts/                    # Deployment scripts
├── .github/workflows/         # GitHub Actions CI/CD
└── docs/                      # Documentation
    ├── DEPLOYMENT.md
    ├── DEPLOYMENT_TRAEFIK.md
    ├── DEPLOYMENT_QUICKSTART.md
    └── RELEASE_PROCESS.md
```

## Architecture

### Custom User System

This project uses a custom user model (`accounts.CustomUser`) with:
- Case-insensitive usernames
- Required email field
- Auto-created user profiles
- Avatar support

### Apps

**accounts**: User authentication, registration, and profile management
- Custom user model with case-insensitive login
- User dashboard with garden statistics
- Profile editing and avatar uploads

**gardens**: Core garden planning functionality
- Interactive garden designer with drag-and-drop
- Plant library with Chicago-specific data
- AI-powered garden suggestions
- Garden sharing and access control
- Yield calculations and statistics

## Environment Variables

For local development, Django uses default settings. For production deployment, configure these environment variables:

```bash
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=garden.passwordspace.com

# Domain Configuration (for Traefik)
DOMAIN_NAME=garden.passwordspace.com

# Database (PostgreSQL for production)
POSTGRES_DB=garden_planner
POSTGRES_USER=garden_user
POSTGRES_PASSWORD=strong-password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# AI Assistant (Optional)
ANTHROPIC_API_KEY=your-anthropic-api-key

# Email Configuration (Optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
```

## Testing

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test accounts
python manage.py test gardens

# Run specific test class
python manage.py test gardens.tests.GardenAccessControlTests

# Run with verbosity
python manage.py test --verbosity=2

# Keep test database for inspection
python manage.py test --keepdb
```

## Production Deployment

This project is configured for production deployment with:
- Docker + Docker Compose
- Traefik reverse proxy with automatic SSL
- PostgreSQL database
- WhiteNoise for static file serving
- GitHub Actions for automated deployment

See documentation:
- **[DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md)** - 10-minute deployment guide
- **[DEPLOYMENT_TRAEFIK.md](DEPLOYMENT_TRAEFIK.md)** - Complete Traefik deployment guide
- **[RELEASE_PROCESS.md](RELEASE_PROCESS.md)** - Version tagging and releases

### Quick Production Deploy

```bash
# On your server
cd /opt/chicago-garden-planner
cp .env.example .env
nano .env  # Configure environment variables
./scripts/deploy.sh
```

### Automated Deployment

The project uses GitHub Actions for automated deployment triggered by version tags:

```bash
./scripts/release.sh 1.0.0 "Initial release"
```

## Chicago-Specific Features

This application is optimized for Chicago's climate (USDA zones 5b/6a):
- **Frost date awareness**: Last frost ~May 15, First frost ~October 15
- **Heat-tolerant varieties**: Plants selected for Midwest summers
- **Seasonal planting calendars**: Zone-specific timing
- **Local pest management**: Chicago-specific pest information
- **Default plants**: 20+ vegetables, herbs, and fruits proven for Chicago

### Default Plant Library

- Tomatoes (6 varieties)
- Peppers (3 varieties)
- Leafy greens (Kale, Lettuce, Spinach, Arugula)
- Root vegetables (Carrots, Beets, Radishes)
- Alliums (Garlic, Onions)
- Herbs (Basil, Cilantro, Parsley)
- Legumes (Beans, Peas)
- Cucurbits (Cucumbers, Zucchini)
- Berries (Strawberries)

Each plant includes:
- Latin name and common names
- Planting season (Spring/Fall/Summer)
- Days to harvest
- Spacing requirements
- Chicago-specific growing notes
- Companion planting relationships
- Pest deterrent properties
- Expected yield estimates

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`python manage.py test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Troubleshooting

### Development Server Won't Start

```bash
# Make sure virtual environment is activated
source garden_env/bin/activate

# Check if another process is using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Try different port
python manage.py runserver 8080
```

### Database Issues

```bash
# Reset database (development only!)
rm db.sqlite3
rm -rf gardens/migrations/0*.py
rm -rf accounts/migrations/0*.py
python manage.py makemigrations
python manage.py migrate
python manage.py populate_default_plants --create-sample-user
```

### Static Files Not Loading

```bash
# Collect static files
python manage.py collectstatic --noinput

# Check STATIC_URL in settings
# Should be '/static/' for development
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check Python version (3.8+ required)
python --version

# Verify virtual environment is activated
which python  # Should point to garden_env/bin/python
```

### AI Assistant Not Working

```bash
# Make sure ANTHROPIC_API_KEY is set
export ANTHROPIC_API_KEY=your-key-here

# Or add to .env file for development
echo "ANTHROPIC_API_KEY=your-key-here" >> .env
```

## License

This project is open source and available for use and modification.

## Support

For issues and questions:
- Review logs and error messages
- Check [CLAUDE.md](CLAUDE.md) for development guidance
- Check deployment documentation for production issues

## Tech Stack

- **Backend**: Django 4.2.7
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **UI Framework**: Bootstrap 5
- **Forms**: django-crispy-forms with Bootstrap 5
- **AI Integration**: Anthropic Claude API
- **Static Files**: WhiteNoise (production)
- **Deployment**: Docker, Docker Compose, Traefik
- **CI/CD**: GitHub Actions

## Acknowledgments

- Plant data optimized for Chicago growing conditions
- Companion planting relationships based on gardening research
- UI/UX designed for ease of use on mobile and desktop
- AI features powered by Anthropic Claude

---

**Happy Gardening! 🌱**

Live at: https://garden.passwordspace.com
