# 🚀 Quick Start - Deploy to garden.passwordspace.com

Deploy Chicago Garden Planner with Traefik in 10 minutes.

## Prerequisites

✅ Server with Traefik already running
✅ DNS: `garden.passwordspace.com` pointing to your server
✅ SSH access to your server

## Step 1: Clone and Configure (3 minutes)

```bash
# SSH to your server
ssh user@your-server

# Create application directory
sudo mkdir -p /opt/chicago-garden-planner
sudo chown $USER:$USER /opt/chicago-garden-planner
cd /opt/chicago-garden-planner

# Clone repository
git clone https://github.com/YOUR-USERNAME/chicago_garden_planner.git .

# Create environment file
cp .env.example .env
nano .env
```

**Edit `.env` with your values:**

```bash
# Domain Configuration
DOMAIN_NAME=garden.passwordspace.com

# Django Configuration
SECRET_KEY=<generate-with-command-below>
ALLOWED_HOSTS=garden.passwordspace.com

# Database Configuration
POSTGRES_PASSWORD=<strong-random-password>

# AI Assistant (Optional)
ANTHROPIC_API_KEY=<your-key-if-needed>
```

**Generate SECRET_KEY:**
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## Step 2: Ensure Traefik Network (1 minute)

```bash
# Create proxy network if it doesn't exist
docker network create proxy || echo "Network already exists"
```

## Step 3: Deploy (5 minutes)

```bash
# Make deploy script executable
chmod +x scripts/deploy.sh

# Deploy application
./scripts/deploy.sh

# Create admin user
docker-compose exec web python manage.py createsuperuser

# Load Chicago-specific plants
docker-compose exec web python manage.py populate_default_plants
```

## Step 4: Verify (1 minute)

```bash
# Check containers are running
docker-compose ps

# Should show:
# ✔ garden_planner_web  - Up (healthy)
# ✔ garden_planner_db   - Up (healthy)

# View logs
docker-compose logs -f web
```

## ✅ Access Your Application

🌐 **Main Site:** https://garden.passwordspace.com
🔐 **Admin Panel:** https://garden.passwordspace.com/admin/

## GitHub Actions Auto-Deployment (Optional)

### Configure Repository Secrets

**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `SERVER_HOST` | Your server IP/hostname | SSH connection target |
| `SERVER_USER` | `ubuntu` or your SSH user | SSH username |
| `SERVER_SSH_KEY` | SSH private key | See below |
| `DEPLOY_PATH` | `/opt/chicago-garden-planner` | App directory |

### Generate SSH Key

On your server:
```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_actions  # Copy entire output → SERVER_SSH_KEY secret
```

### Deploy with Version Tags

```bash
# Use the release script
./scripts/release.sh 1.0.0 "Initial production release"

# Or manually
git tag -a v1.0.0 -m "Initial production release"
git push origin v1.0.0
```

GitHub Actions will automatically:
1. Build Docker image
2. Push to GitHub Container Registry
3. Deploy to your server
4. Run migrations
5. Collect static files

## 📊 Common Commands

### View Logs
```bash
docker-compose logs -f web     # Application logs
docker-compose logs -f db      # Database logs
docker-compose logs -f         # All logs
```

### Restart Application
```bash
docker-compose restart web     # Restart app only
docker-compose restart         # Restart all services
```

### Django Management
```bash
# Django shell
docker-compose exec web python manage.py shell

# Create migrations
docker-compose exec web python manage.py makemigrations

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### Database Operations
```bash
# Backup database
docker-compose exec db pg_dump -U garden_user garden_planner > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20250123.sql | docker-compose exec -T db psql -U garden_user garden_planner

# Access database shell
docker-compose exec db psql -U garden_user garden_planner
```

### Update Application
```bash
cd /opt/chicago-garden-planner
git pull origin main
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

## 🔧 Troubleshooting

### Site Not Accessible

1. **Check containers:**
   ```bash
   docker-compose ps
   # Both should show "Up (healthy)"
   ```

2. **Check Traefik routing:**
   ```bash
   docker logs traefik | grep garden
   # Should see routing rules for garden.passwordspace.com
   ```

3. **Verify DNS:**
   ```bash
   nslookup garden.passwordspace.com
   # Should point to your server IP
   ```

4. **Check web logs:**
   ```bash
   docker-compose logs web
   ```

5. **Verify proxy network:**
   ```bash
   docker network ls | grep proxy
   docker inspect garden_planner_web | grep -A 20 Networks
   ```

### Database Connection Issues

```bash
# Check database health
docker-compose ps db

# View database logs
docker-compose logs db

# Test connection from web container
docker-compose exec web python manage.py dbshell
```

### Static Files Not Loading

```bash
# Recollect static files
docker-compose exec web python manage.py collectstatic --noinput --clear

# Verify WhiteNoise is installed
docker-compose exec web pip show whitenoise

# Check static files exist
docker-compose exec web ls -la /app/staticfiles/
```

### Traefik Configuration Issues

**Verify your Traefik has:**
- External `proxy` network: `docker network ls | grep proxy`
- `websecure` entrypoint on port 443
- Certificate resolver named `myresolver`

**Check Traefik labels are set:**
```bash
docker inspect garden_planner_web | grep -A 30 Labels
```

### SSL Certificate Issues

```bash
# Check Traefik certificate resolver
docker logs traefik | grep -i acme
docker logs traefik | grep -i certificate

# Verify DNS is correct
nslookup garden.passwordspace.com

# Check Let's Encrypt rate limits
# https://letsencrypt.org/docs/rate-limits/
```

## 📐 Architecture

```
Internet
   ↓ HTTPS
Traefik (external, manages SSL)
   ↓ proxy network
Django/Gunicorn + WhiteNoise
   ↓ backend network
PostgreSQL
```

**Components:**
- **Traefik**: SSL termination, routing, load balancing
- **Django/Gunicorn**: Application server (port 8000, internal)
- **WhiteNoise**: Serves static files with compression
- **PostgreSQL 16**: Database with persistent volume

**No Nginx needed!** Traefik handles all routing and SSL.

## 🔒 Security Checklist

- ✅ Strong SECRET_KEY (50+ characters)
- ✅ Strong POSTGRES_PASSWORD
- ✅ HTTPS enabled via Traefik
- ✅ Secure cookies (SESSION_COOKIE_SECURE=True)
- ✅ CSRF protection (CSRF_COOKIE_SECURE=True)
- ✅ HSTS headers (31536000 seconds)
- ✅ Database on internal network only
- ✅ No exposed database ports

## 📦 What Gets Deployed

**Docker Images:**
- `garden_planner_web`: Django application
- `postgres:16-alpine`: Database

**Volumes (Persistent Data):**
- `postgres_data`: Database files
- `static_volume`: Static files (CSS, JS, images)
- `media_volume`: User uploads (avatars, etc.)

**Networks:**
- `proxy`: External network shared with Traefik
- `backend`: Internal network for web ↔ database

## 🎯 Next Steps

After deployment:

1. **Test thoroughly:**
   - Create user accounts
   - Design a garden
   - Test plant library
   - Try AI assistant features

2. **Configure email:**
   - Update `.env` with SMTP settings
   - Test password reset emails

3. **Set up backups:**
   ```bash
   # Add to crontab
   0 2 * * * cd /opt/chicago-garden-planner && docker-compose exec -T db pg_dump -U garden_user garden_planner > /backup/garden_$(date +\%Y\%m\%d).sql
   ```

4. **Monitor logs:**
   ```bash
   docker-compose logs -f --tail=100
   ```

5. **Consider adding:**
   - Redis for caching
   - Monitoring/alerting
   - Regular security updates

## 📚 Additional Documentation

- **[DEPLOYMENT_TRAEFIK.md](DEPLOYMENT_TRAEFIK.md)**: Complete Traefik deployment guide
- **[RELEASE_PROCESS.md](RELEASE_PROCESS.md)**: Version tagging and releases
- **[DEPLOYMENT.md](DEPLOYMENT.md)**: General deployment information
- **[CLAUDE.md](CLAUDE.md)**: Development guide

## 🆘 Need Help?

1. Check logs: `docker-compose logs -f`
2. Verify configuration: `docker-compose config`
3. Check Traefik: `docker logs traefik`
4. Review documentation in links above

## 🎉 Success!

Your Chicago Garden Planner is now live at:

**https://garden.passwordspace.com**

Features:
- ✅ Chicago-specific plant library (zones 5b/6a)
- ✅ Drag-and-drop garden designer
- ✅ Companion planting recommendations
- ✅ AI-powered garden layout suggestions
- ✅ Yield calculations and statistics
- ✅ Garden sharing with access control
- ✅ Responsive design for mobile/tablet

Happy gardening! 🌱
