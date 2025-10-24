# 🚀 Deployment Guide - Chicago Garden Planner

This guide covers deploying the Chicago Garden Planner to a production server using Docker Compose and GitHub Actions.

## 📋 Prerequisites

- A Linux server (Ubuntu 20.04+ recommended)
- Docker and Docker Compose installed on your server
- A domain name pointing to your server (optional but recommended for SSL)
- SSH access to your server
- GitHub repository with Actions enabled

## 🏗️ Architecture

```
Internet → Nginx (80/443) → Django/Gunicorn (8000) → PostgreSQL (5432)
                    ↓
              Static Files & Media
```

**Components:**
- **Nginx**: Reverse proxy, serves static/media files, handles SSL
- **Django + Gunicorn**: Application server
- **PostgreSQL**: Production database
- **Certbot**: Automatic SSL certificate renewal

## 🔧 Server Setup

### 1. Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 2. Create Application Directory

```bash
sudo mkdir -p /opt/chicago-garden-planner
sudo chown $USER:$USER /opt/chicago-garden-planner
cd /opt/chicago-garden-planner
```

### 3. Clone Repository (or set up for GitHub Actions)

```bash
git clone https://github.com/YOUR-USERNAME/chicago_garden_planner.git .
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your actual values
nano .env
```

**Important `.env` variables to set:**

```bash
# Generate a secure secret key
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Your domain
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database password (generate a strong password)
POSTGRES_PASSWORD=your_secure_database_password_here

# Email (if using email features)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
```

### 5. Deploy the Application

```bash
# Make scripts executable
chmod +x scripts/deploy.sh

# Run deployment
./scripts/deploy.sh
```

### 6. Create Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

### 7. Load Default Data

```bash
docker-compose exec web python manage.py populate_default_plants
docker-compose exec web python manage.py create_companion_relationship
```

## 🔒 SSL/HTTPS Setup

### Option 1: Let's Encrypt (Recommended)

```bash
# Run SSL setup script
chmod +x scripts/setup-ssl.sh
./scripts/setup-ssl.sh yourdomain.com your-email@example.com

# Edit nginx configuration
nano nginx/conf.d/app.conf

# Uncomment the HTTPS server block and update domain
# Comment out the HTTP server block (or keep redirect only)

# Update .env for HTTPS
nano .env
```

Add to `.env`:
```bash
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
```

```bash
# Restart services
docker-compose restart
```

### Option 2: Existing SSL Certificates

Place your certificates in:
- `/etc/letsencrypt/live/yourdomain.com/fullchain.pem`
- `/etc/letsencrypt/live/yourdomain.com/privkey.pem`

And update `nginx/conf.d/app.conf` accordingly.

## 🤖 GitHub Actions Setup

### 1. Add GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SERVER_HOST` | Your server IP/domain | `123.45.67.89` |
| `SERVER_USER` | SSH username | `ubuntu` |
| `SERVER_SSH_KEY` | Private SSH key | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SERVER_PORT` | SSH port (optional) | `22` |
| `DEPLOY_PATH` | App directory on server | `/opt/chicago-garden-planner` |

### 2. Generate SSH Key for GitHub Actions

On your server:

```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions

# Add public key to authorized_keys
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys

# Display private key (copy this to GitHub Secret SERVER_SSH_KEY)
cat ~/.ssh/github_actions
```

### 3. Test Deployment

```bash
# Push to main branch
git add .
git commit -m "Setup deployment"
git push origin main
```

The GitHub Action will automatically:
1. Build Docker image
2. Push to GitHub Container Registry
3. SSH to your server
4. Pull latest image
5. Run migrations
6. Restart containers

## 📊 Monitoring and Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f nginx
docker-compose logs -f db
```

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U garden_user garden_planner > backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose exec -T db psql -U garden_user garden_planner < backup_20241023.sql
```

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate
```

### Useful Commands

```bash
# Restart all services
docker-compose restart

# Stop all services
docker-compose down

# View running containers
docker-compose ps

# Django shell
docker-compose exec web python manage.py shell

# Database shell
docker-compose exec db psql -U garden_user garden_planner

# Clear cache
docker-compose exec web python manage.py clear_cache

# Create database backup
docker-compose exec db pg_dump -U garden_user garden_planner > backup.sql
```

## 🔥 Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs web

# Check if ports are in use
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443
```

### Database connection errors

```bash
# Check database is running
docker-compose ps db

# Check environment variables
docker-compose exec web env | grep POSTGRES
```

### Static files not loading

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check nginx logs
docker-compose logs nginx
```

### SSL certificate renewal

```bash
# Manual renewal
docker-compose run --rm certbot renew

# Check certificate expiry
docker-compose run --rm certbot certificates
```

## 📈 Performance Optimization

### Enable Gzip Compression
Already enabled in nginx configuration.

### Database Connection Pooling
Already configured with `CONN_MAX_AGE=600` in production settings.

### Static File Caching
Already configured in nginx with appropriate cache headers.

### Optional: Add Redis for Caching

Uncomment Redis configuration in `docker-compose.yml` and `settings_production.py`.

## 🔐 Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong database password
- [ ] Enable HTTPS/SSL
- [ ] Set SECURE_SSL_REDIRECT=True
- [ ] Set SESSION_COOKIE_SECURE=True
- [ ] Set CSRF_COOKIE_SECURE=True
- [ ] Configure firewall (UFW)
- [ ] Keep Docker images updated
- [ ] Regular database backups
- [ ] Monitor logs for suspicious activity

## 📞 Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review Django settings in `garden_planner/settings_production.py`
- Check nginx configuration in `nginx/conf.d/app.conf`

## 📝 License

See LICENSE file for details.
