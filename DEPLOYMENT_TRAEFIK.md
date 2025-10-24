# Deployment with Traefik

This guide covers deploying Chicago Garden Planner with Traefik as the reverse proxy.

## Prerequisites

1. **Server with Traefik installed and running**
   - Traefik must be configured with an external `proxy` network
   - SSL certificate resolver named `myresolver` configured
   - Traefik should be listening on `websecure` entrypoint (port 443)

2. **Server access**
   - SSH access to your server
   - Docker and Docker Compose installed
   - Domain name pointing to your server

3. **GitHub setup**
   - Repository forked/cloned
   - GitHub Actions enabled

## Quick Start

### 1. Set Up Application Directory

```bash
# SSH to your server
ssh user@your-server.com

# Create application directory
sudo mkdir -p /opt/chicago-garden-planner
sudo chown $USER:$USER /opt/chicago-garden-planner
cd /opt/chicago-garden-planner

# Clone repository
git clone https://github.com/YOUR-USERNAME/chicago_garden_planner.git .
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

**Required settings in `.env`:**

```bash
# Domain Configuration
DOMAIN_NAME=garden.yourdomain.com

# Django Configuration
SECRET_KEY=your-very-long-random-secret-key-at-least-50-characters
DEBUG=False
ALLOWED_HOSTS=garden.yourdomain.com

# Database Configuration
POSTGRES_DB=garden_planner
POSTGRES_USER=garden_user
POSTGRES_PASSWORD=your-strong-database-password

# Security (Traefik handles SSL)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000

# AI Assistant (Optional)
ANTHROPIC_API_KEY=your-anthropic-api-key
```

**Generate a strong SECRET_KEY:**
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 3. Ensure Traefik Network Exists

```bash
# Check if proxy network exists
docker network ls | grep proxy

# If it doesn't exist, create it
docker network create proxy
```

### 4. Deploy Application

```bash
# Build and start containers
docker-compose up -d

# Wait for database to be ready (about 30 seconds)
docker-compose logs -f db

# Once database is ready, run initial setup
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py populate_default_plants
```

### 5. Verify Deployment

```bash
# Check container status
docker-compose ps

# Should show:
# garden_planner_web - Up (healthy)
# garden_planner_db  - Up (healthy)

# View logs
docker-compose logs -f web

# Access your site
# https://garden.yourdomain.com
```

## GitHub Actions Deployment

### Configure Repository Secrets

Go to: `https://github.com/YOUR-USERNAME/chicago_garden_planner/settings/secrets/actions`

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `SERVER_HOST` | `your-server.com` | Your server hostname/IP |
| `SERVER_USER` | `ubuntu` | SSH username |
| `SERVER_SSH_KEY` | `<private key>` | SSH private key for authentication |
| `DEPLOY_PATH` | `/opt/chicago-garden-planner` | Application directory path |

**Generate SSH key on server:**
```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_actions  # Copy this entire output as SERVER_SSH_KEY
```

### Deploy with Version Tags

```bash
# Create and push a version tag
./scripts/release.sh 1.0.0 "Initial production release"

# Or manually
git tag -a v1.0.0 -m "Initial production release"
git push origin v1.0.0
```

This will trigger GitHub Actions to:
1. Build Docker image
2. Push to GitHub Container Registry
3. SSH to server
4. Pull latest image
5. Restart containers
6. Run migrations
7. Collect static files

## Architecture

### Container Structure

```
┌─────────────────────────────────────────┐
│           Traefik (External)            │
│  - SSL Termination                      │
│  - HTTP → HTTPS Redirect                │
│  - Routing: garden.yourdomain.com       │
└────────────────┬────────────────────────┘
                 │ proxy network
                 ▼
┌─────────────────────────────────────────┐
│     garden_planner_web                  │
│  - Django + Gunicorn                    │
│  - WhiteNoise (static files)            │
│  - Port 8000 (internal)                 │
└────────────────┬────────────────────────┘
                 │ backend network
                 ▼
┌─────────────────────────────────────────┐
│     garden_planner_db                   │
│  - PostgreSQL 16                        │
│  - Persistent volume                    │
└─────────────────────────────────────────┘
```

### Static Files

Static files are served by Django using **WhiteNoise** middleware:
- Efficient gzip compression
- Cache-friendly file hashing
- No separate web server needed for static files
- Media files (user uploads) served by Django/Gunicorn

## Traefik Configuration

The application expects Traefik to be configured with:

1. **External network:** `proxy`
2. **Entrypoint:** `websecure` (port 443)
3. **Certificate resolver:** `myresolver` (Let's Encrypt)

### Example Traefik docker-compose.yml

If you don't have Traefik set up yet, here's a basic configuration:

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    container_name: traefik
    restart: unless-stopped
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.tlschallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=your@email.com"
      - "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik-certificates:/letsencrypt
    networks:
      - proxy

networks:
  proxy:
    external: true

volumes:
  traefik-certificates:
```

## Common Operations

### View Logs

```bash
# All logs
docker-compose logs -f

# Web server only
docker-compose logs -f web

# Database only
docker-compose logs -f db

# Last 100 lines
docker-compose logs --tail=100
```

### Restart Application

```bash
# Restart all services
docker-compose restart

# Restart web only
docker-compose restart web

# Full rebuild
docker-compose down
docker-compose up -d --build
```

### Database Operations

```bash
# Create backup
docker-compose exec db pg_dump -U garden_user garden_planner > backup_$(date +%Y%m%d).sql

# Restore backup
cat backup_20250115.sql | docker-compose exec -T db psql -U garden_user garden_planner

# Access database shell
docker-compose exec db psql -U garden_user garden_planner

# Run migrations
docker-compose exec web python manage.py migrate

# Create new migration
docker-compose exec web python manage.py makemigrations
```

### Django Management Commands

```bash
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Load default plants
docker-compose exec web python manage.py populate_default_plants

# Django shell
docker-compose exec web python manage.py shell

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### Update Application

```bash
# Pull latest changes
cd /opt/chicago-garden-planner
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

## Monitoring

### Check Container Health

```bash
# Container status
docker-compose ps

# Health checks
docker inspect garden_planner_web | grep -A 10 Health
docker inspect garden_planner_db | grep -A 10 Health
```

### Resource Usage

```bash
# CPU and memory usage
docker stats

# Disk usage
docker system df
```

### Access Logs

Django logs go to stdout/stderr and are captured by Docker:

```bash
# Real-time logs
docker-compose logs -f web

# Filter by level
docker-compose logs web | grep ERROR
docker-compose logs web | grep WARNING
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs web

# Common issues:
# 1. Missing environment variables
docker-compose config

# 2. Database not ready
docker-compose logs db

# 3. Port conflicts
docker ps -a
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Test database connection
docker-compose exec web python manage.py dbshell

# Check database logs
docker-compose logs db
```

### Static Files Not Loading

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check WhiteNoise is installed
docker-compose exec web pip list | grep whitenoise

# Verify static files exist
docker-compose exec web ls -la /app/staticfiles/
```

### Traefik Routing Issues

```bash
# Check Traefik logs
docker logs traefik

# Verify proxy network exists
docker network ls | grep proxy

# Check container is on proxy network
docker inspect garden_planner_web | grep -A 20 Networks

# Verify labels are set
docker inspect garden_planner_web | grep -A 30 Labels
```

### SSL Certificate Issues

```bash
# Check Traefik certificate resolver
docker logs traefik | grep -i certificate

# Verify domain DNS points to server
nslookup garden.yourdomain.com

# Check Let's Encrypt rate limits
# https://letsencrypt.org/docs/rate-limits/
```

## Security Best Practices

1. **Environment Variables**
   - Never commit `.env` file to git
   - Use strong passwords (20+ characters)
   - Rotate secrets regularly

2. **Database**
   - Use strong POSTGRES_PASSWORD
   - Keep database on internal network only
   - Regular backups

3. **SSL/HTTPS**
   - Always use HTTPS in production
   - Enable HSTS headers
   - Keep Traefik updated

4. **Updates**
   - Keep Docker images updated
   - Monitor security advisories
   - Test updates in development first

## Backup Strategy

### Automated Backups

Create a cron job for regular backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /opt/chicago-garden-planner && docker-compose exec -T db pg_dump -U garden_user garden_planner > /backup/garden_$(date +\%Y\%m\%d).sql
```

### Manual Backup

```bash
# Full database backup
docker-compose exec db pg_dump -U garden_user garden_planner > backup.sql

# Backup media files
tar -czf media_backup.tar.gz media/

# Backup environment
cp .env .env.backup
```

## Rollback

### Rollback to Previous Version

```bash
# Pull specific Docker image version
docker pull ghcr.io/YOUR-USERNAME/chicago-garden-planner:v1.0.0

# Update docker-compose.yml to pin version
# Change: image: ghcr.io/YOUR-USERNAME/chicago-garden-planner:latest
# To:     image: ghcr.io/YOUR-USERNAME/chicago-garden-planner:v1.0.0

# Restart
docker-compose down
docker-compose up -d
```

### Rollback Database Migration

```bash
# List migrations
docker-compose exec web python manage.py showmigrations

# Rollback to specific migration
docker-compose exec web python manage.py migrate gardens 0005_previous_migration
```

## Support

For issues and questions:
- Review logs: `docker-compose logs -f`
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup
- Verify Traefik configuration
- Check GitHub Actions logs for deployment issues

## Next Steps

After deployment:
- Configure email settings for password resets
- Set up regular database backups
- Configure monitoring/alerting
- Review security settings
- Consider adding Redis for caching
