# 🚀 Quick Start - Deploy in 15 Minutes

This is a condensed deployment guide. For full details, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Prerequisites

- Ubuntu/Debian server with root/sudo access
- Domain name (optional, can use IP for testing)
- SSH access configured

## Step 1: Install Docker (2 minutes)

```bash
# One-line install
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in for group changes
exit
```

## Step 2: Set Up Application (3 minutes)

```bash
# Create directory
sudo mkdir -p /opt/chicago-garden-planner
sudo chown $USER:$USER /opt/chicago-garden-planner
cd /opt/chicago-garden-planner

# Clone repository
git clone https://github.com/YOUR-USERNAME/chicago_garden_planner.git .

# Create .env file
cp .env.example .env
nano .env
```

**Minimum required in `.env`:**

```bash
SECRET_KEY=your-long-random-secret-key-here-at-least-50-chars
ALLOWED_HOSTS=your-domain.com,your-ip-address
POSTGRES_PASSWORD=strong-database-password-here
DEBUG=False
```

## Step 3: Deploy (5 minutes)

```bash
# Deploy
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Wait for containers to start (about 2-3 minutes)

# Create admin user
docker-compose exec web python manage.py createsuperuser

# Load default plants
docker-compose exec web python manage.py populate_default_plants
```

## Step 4: Configure GitHub Actions (5 minutes)

### A. Generate SSH Key on Server

```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_actions  # Copy this entire output
```

### B. Add GitHub Secrets

Go to: `https://github.com/YOUR-USERNAME/chicago_garden_planner/settings/secrets/actions`

Click "New repository secret" and add:

| Name | Value |
|------|-------|
| `SERVER_HOST` | Your server IP or domain |
| `SERVER_USER` | Your SSH username (e.g., `ubuntu`) |
| `SERVER_SSH_KEY` | Paste the private key from step A |
| `DEPLOY_PATH` | `/opt/chicago-garden-planner` |

### C. Test Automatic Deployment

Deployments are triggered by creating version tags:

```bash
# Create a version tag
git tag v1.0.0
git push origin v1.0.0

# Or use this helper command
git tag -a v1.0.0 -m "Initial production release"
git push origin v1.0.0
```

Go to GitHub → Actions tab and watch your deployment! 🎉

**Future deployments:**
```bash
# When you're ready to deploy new changes:
git tag v1.0.1
git push origin v1.0.1

# Or for a major release:
git tag v2.0.0
git push origin v2.0.0
```

**Note:** The workflow also supports manual deployment via the Actions tab.

## ✅ Verify Deployment

```bash
# Check all containers are running
docker-compose ps

# Should see:
# ✔ garden_planner_web
# ✔ garden_planner_db
# ✔ garden_planner_nginx

# Visit your site
curl http://your-domain.com
# or
curl http://your-ip-address
```

## 🔒 Optional: Enable HTTPS (5 minutes)

```bash
# Install SSL certificate
chmod +x scripts/setup-ssl.sh
./scripts/setup-ssl.sh your-domain.com your-email@example.com

# Edit nginx config
nano nginx/conf.d/app.conf
# Uncomment the HTTPS server block
# Update "your-domain.com" to your actual domain

# Update .env
nano .env
# Add:
# SECURE_SSL_REDIRECT=True
# SESSION_COOKIE_SECURE=True
# CSRF_COOKIE_SECURE=True

# Restart
docker-compose restart
```

## 📊 Common Commands

```bash
# View logs
docker-compose logs -f

# Restart application
docker-compose restart

# Run Django management command
docker-compose exec web python manage.py <command>

# Access Django shell
docker-compose exec web python manage.py shell

# Database backup
docker-compose exec db pg_dump -U garden_user garden_planner > backup.sql
```

## 🆘 Troubleshooting

### Can't access the site?

```bash
# Check firewall
sudo ufw status
sudo ufw allow 80
sudo ufw allow 443

# Check containers
docker-compose ps
docker-compose logs nginx
```

### Database errors?

```bash
# Check database is running
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Need to reset everything?

```bash
# Stop and remove everything
docker-compose down -v

# Start fresh
./scripts/deploy.sh
```

## 🎉 You're Done!

Your Chicago Garden Planner is now:
- ✅ Running in production
- ✅ Backed by PostgreSQL
- ✅ Serving via Nginx
- ✅ Auto-deploying from GitHub

**Access your site:**
- Frontend: `http://your-domain.com`
- Admin: `http://your-domain.com/admin`

**Next steps:**
- Set up SSL/HTTPS (see above)
- Configure email for password resets
- Set up regular database backups
- Monitor logs and performance

For detailed information, see [DEPLOYMENT.md](DEPLOYMENT.md).
