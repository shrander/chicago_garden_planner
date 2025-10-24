# 🚀 Release Process

This document describes how to create new releases and deploy to production.

## Quick Release

Use the release script for an easy, guided release process:

```bash
./scripts/release.sh 1.0.0 "Initial production release"
```

This will:
1. ✅ Validate version format
2. ✅ Check for uncommitted changes
3. ✅ Pull latest from remote
4. ✅ Show recent commits
5. ✅ Create annotated git tag
6. ✅ Push tag to trigger deployment
7. ✅ Provide GitHub Actions link

## Manual Release

If you prefer to create releases manually:

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tag to trigger deployment
git push origin v1.0.0
```

## Semantic Versioning

We follow [Semantic Versioning](https://semver.org/):

**Format:** `vMAJOR.MINOR.PATCH`

- **MAJOR** (v2.0.0): Breaking changes, incompatible API changes
- **MINOR** (v1.1.0): New features, backwards-compatible
- **PATCH** (v1.0.1): Bug fixes, backwards-compatible

### Examples

```bash
# Bug fix
./scripts/release.sh 1.0.1 "Fix garden sharing permission bug"

# New feature
./scripts/release.sh 1.1.0 "Add plant companion planting suggestions"

# Breaking change
./scripts/release.sh 2.0.0 "Redesign database schema for multi-user gardens"
```

## Release Checklist

Before creating a release:

- [ ] All tests passing locally: `python manage.py test`
- [ ] All changes committed and pushed to main
- [ ] CHANGELOG.md updated (if you maintain one)
- [ ] Database migrations created and tested
- [ ] Environment variables documented in .env.example
- [ ] Documentation updated
- [ ] Security vulnerabilities addressed

## Deployment Pipeline

When you push a version tag, GitHub Actions will:

1. **Build** - Create Docker image with your code
2. **Tag** - Tag image with: `latest`, version (e.g., `v1.0.0`), and commit SHA
3. **Push** - Upload to GitHub Container Registry
4. **Deploy** - SSH to server and:
   - Pull latest image
   - Stop old containers
   - Start new containers
   - Run database migrations
   - Collect static files
5. **Verify** - Check container health
6. **Notify** - Show deployment status and version

## Monitoring Deployment

### View in GitHub

1. Go to your repository on GitHub
2. Click "Actions" tab
3. Find your deployment workflow
4. Watch real-time progress

### View on Server

```bash
# SSH to your server
ssh user@your-server.com

# Navigate to app directory
cd /opt/chicago-garden-planner

# View deployment logs
docker-compose logs -f web

# Check container status
docker-compose ps

# View recent containers
docker ps -a
```

## Rollback

If something goes wrong, you can rollback to a previous version:

### Option 1: Deploy Previous Tag

```bash
# Find previous tags
git tag -l "v*"

# Re-push a previous tag (this will trigger redeployment)
git push origin v1.0.0 --force
```

### Option 2: Manual Rollback on Server

```bash
# SSH to server
ssh user@your-server.com
cd /opt/chicago-garden-planner

# Pull specific version
docker pull ghcr.io/YOUR-USERNAME/chicago-garden-planner:v1.0.0

# Update docker-compose to use specific version
# Edit docker-compose.yml and change:
#   image: ghcr.io/YOUR-USERNAME/chicago-garden-planner:v1.0.0

# Restart
docker-compose down
docker-compose up -d
```

### Option 3: Database Rollback

If you need to rollback database migrations:

```bash
# On server
docker-compose exec web python manage.py showmigrations

# Rollback to specific migration
docker-compose exec web python manage.py migrate app_name migration_name
```

## Hotfix Process

For urgent production fixes:

```bash
# 1. Create hotfix branch
git checkout -b hotfix/critical-bug-fix

# 2. Make minimal fix
# ... edit files ...

# 3. Test thoroughly
python manage.py test

# 4. Commit
git add .
git commit -m "Fix critical authentication bug"

# 5. Merge to main
git checkout main
git merge hotfix/critical-bug-fix

# 6. Release patch version
./scripts/release.sh 1.0.1 "Hotfix: Fix authentication bug"

# 7. Clean up
git branch -d hotfix/critical-bug-fix
```

## Pre-release Testing

Test deployments without affecting production:

### Option 1: Use Dev Compose

```bash
# Test with development docker-compose
docker-compose -f docker-compose.dev.yml up --build

# Verify everything works
# Then create production release
```

### Option 2: Staging Environment

If you have a staging server:

```bash
# Create a pre-release tag
git tag -a v1.1.0-rc.1 -m "Release candidate 1"
git push origin v1.1.0-rc.1

# Deploy to staging
# Test thoroughly

# Create production release
git tag -a v1.1.0 -m "Production release"
git push origin v1.1.0
```

## Versioning Strategy

### Starting Out
- Start with `v1.0.0` for initial production release
- Use `v0.x.x` for pre-production/beta releases

### Typical Progression
```
v1.0.0  - Initial release
v1.0.1  - Bug fix
v1.0.2  - Another bug fix
v1.1.0  - New feature added
v1.1.1  - Bug fix in new feature
v1.2.0  - Another new feature
v2.0.0  - Major rewrite or breaking change
```

## Release Notes

Consider creating release notes for each version:

```bash
# On GitHub
1. Go to Releases
2. Click "Draft a new release"
3. Choose your tag
4. Write release notes
5. Publish
```

Example release notes template:
```markdown
## What's New in v1.1.0

### ✨ New Features
- Added plant companion suggestions
- Improved garden sharing UI

### 🐛 Bug Fixes
- Fixed issue with date picker on mobile
- Resolved database query performance issues

### 📝 Documentation
- Updated deployment guide
- Added API documentation

### ⚠️ Breaking Changes
None

### 📦 Dependencies
- Updated Django to 4.2.8
- Updated Pillow to 10.1.0
```

## Best Practices

1. **Always test before releasing**
2. **Use descriptive tag messages**
3. **Follow semantic versioning**
4. **Keep CHANGELOG updated**
5. **Monitor deployments**
6. **Have a rollback plan**
7. **Release during low-traffic times**
8. **Communicate with team**

## Troubleshooting

### Tag Already Exists

```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin :refs/tags/v1.0.0

# Create new tag
git tag -a v1.0.0 -m "Your message"
git push origin v1.0.0
```

### Deployment Failed

1. Check GitHub Actions logs
2. SSH to server and check Docker logs
3. Verify environment variables
4. Check database connectivity
5. Review recent code changes

### Need to Cancel Deployment

Currently running deployments cannot be cancelled mid-flight, but you can:
1. Let it complete
2. Immediately rollback to previous version
3. Or manually stop on server: `docker-compose down`

## Support

For deployment issues:
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup
- Review GitHub Actions logs
- Check server logs: `docker-compose logs -f`
- Verify environment variables match .env.example
