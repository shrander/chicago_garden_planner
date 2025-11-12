# Self-Hosted GitHub Actions Runner Setup

This guide explains how to set up automated deployments using a self-hosted GitHub Actions runner on your NanoPi server **without exposing SSH to the internet**.

## Architecture Overview

```
┌─────────────────┐
│  Your Mac       │  1. Push code changes
│  (Development)  │  2. Run: ./scripts/release.sh 1.0.0
└────────┬────────┘
         │
         │ Git push with tag "v1.0.0"
         ▼
┌─────────────────────────┐
│  GitHub Repository      │  3. Tag triggers workflow
│  (github.com)           │
└────────┬────────────────┘
         │
         │ GitHub notifies runner
         │ (outbound connection from server)
         ▼
┌─────────────────────────────────────┐
│  NanoPi Server                      │
│  (GitHub Actions Runner)            │
│                                     │
│  4. Runner pulls job from GitHub    │
│  5. Checks out code                 │
│  6. Builds Docker image             │
│  7. Deploys locally                 │
│  8. Reports status back to GitHub   │
└─────────────────────────────────────┘
```

**Key Benefits:**
- ✅ No SSH exposed to internet
- ✅ Server initiates all connections (outbound only)
- ✅ Automated deployments from anywhere
- ✅ Version tracking with git tags
- ✅ Deployment logs visible in GitHub

## Prerequisites

1. **GitHub Personal Access Token (PAT)**
   - Go to: https://github.com/settings/tokens/new
   - Select scopes: `repo` and `workflow`
   - Generate token and save it securely

2. **Server Requirements**
   - Docker and Docker Compose installed
   - Git configured
   - Sudo access
   - Outbound HTTPS access (port 443)

## Installation Steps

### Step 1: Run Setup Script on NanoPi

SSH into your NanoPi server and run:

```bash
cd ~/workspace/chicago-garden-planner
./scripts/setup-github-runner.sh
```

The script will:
1. Detect your architecture (ARM64)
2. Download the latest GitHub Actions runner
3. Ask for your repository details
4. Ask for your GitHub Personal Access Token
5. Register the runner with GitHub
6. Install it as a systemd service
7. Start the runner automatically

### Step 2: Verify Runner Registration

1. Go to your repository settings:
   ```
   https://github.com/YOUR_USERNAME/chicago_garden_planner/settings/actions/runners
   ```

2. You should see a runner named `nanopi-HOSTNAME` with status "Idle"

3. The runner should have these labels:
   - `self-hosted`
   - `Linux`
   - `ARM64`
   - `production`

## Using the Automated Deployment

### From Your Mac (or any machine)

1. **Make code changes and commit:**
   ```bash
   git add .
   git commit -m "Your changes"
   git push
   ```

2. **Create a release:**
   ```bash
   ./scripts/release.sh 1.0.0 "Initial production release"
   ```

3. **Watch the deployment:**
   - GitHub Actions: https://github.com/YOUR_USERNAME/chicago_garden_planner/actions
   - The runner on your NanoPi will automatically:
     - Pull the latest code
     - Build the Docker image
     - Stop old containers
     - Start new containers
     - Run migrations
     - Collect static files

4. **Verify deployment:**
   - Visit: https://garden.passwordspace.com
   - Check the version tag deployed

## Runner Management

### Check Runner Status

```bash
# On your NanoPi server
sudo ~/actions-runner/svc.sh status
```

### View Runner Logs

```bash
# Real-time logs
journalctl -u actions.runner.* -f

# Last 100 lines
journalctl -u actions.runner.* -n 100
```

### Restart Runner

```bash
sudo ~/actions-runner/svc.sh restart
```

### Stop Runner

```bash
sudo ~/actions-runner/svc.sh stop
```

### Start Runner

```bash
sudo ~/actions-runner/svc.sh start
```

### Remove Runner

If you need to uninstall:

```bash
cd ~/actions-runner
sudo ./svc.sh stop
sudo ./svc.sh uninstall
./config.sh remove --token YOUR_REMOVAL_TOKEN
```

## Workflow Details

The workflow (`.github/workflows/deploy.yml`) runs these steps:

1. **Checkout code** - Gets the tagged version
2. **Extract version** - Identifies the release version
3. **Stop containers** - Gracefully stops running containers
4. **Build image** - Builds new Docker image locally
5. **Start containers** - Starts containers with new image
6. **Wait for health** - Ensures containers are running
7. **Run migrations** - Applies database changes
8. **Collect static** - Gathers static files
9. **Check status** - Verifies deployment
10. **Notify** - Reports success/failure

## Troubleshooting

### Runner Not Showing Up in GitHub

1. Check runner service status:
   ```bash
   sudo ~/actions-runner/svc.sh status
   ```

2. Check logs for errors:
   ```bash
   journalctl -u actions.runner.* -n 50
   ```

3. Verify internet connectivity:
   ```bash
   curl -I https://github.com
   ```

### Deployment Fails

1. **Check GitHub Actions logs:**
   - Go to: https://github.com/YOUR_USERNAME/chicago_garden_planner/actions
   - Click on the failed run
   - Review step logs

2. **Check Docker on server:**
   ```bash
   cd ~/workspace/chicago-garden-planner
   docker compose ps
   docker compose logs web
   ```

3. **Check runner logs:**
   ```bash
   journalctl -u actions.runner.* -n 200
   ```

### Runner Goes Offline

The runner might go offline if:
- Server restarts (should auto-start via systemd)
- Network issues
- Runner service crashed

**To fix:**
```bash
sudo ~/actions-runner/svc.sh restart
```

### Update Runner

To update to the latest runner version:

```bash
cd ~/actions-runner
sudo ./svc.sh stop
sudo ./svc.sh uninstall

# Re-run the setup script
cd ~/workspace/chicago-garden-planner
./scripts/setup-github-runner.sh
```

## Security Considerations

### What's Exposed?

- ✅ **Nothing!** The runner connects OUT to GitHub
- ✅ No inbound SSH required
- ✅ No inbound connections at all
- ✅ Runner authenticates to GitHub using tokens

### Best Practices

1. **Use a dedicated user** - Don't run as root
2. **Limit runner permissions** - Runner only needs access to the repo directory
3. **Keep runner updated** - Update periodically for security patches
4. **Rotate PAT tokens** - Change your Personal Access Token regularly
5. **Monitor logs** - Check runner logs for suspicious activity

### Firewall Rules

Only outbound connections needed:
- Port 443 (HTTPS) to github.com
- Port 443 (HTTPS) to api.github.com

No inbound ports required for the runner!

## Comparison: Manual vs Automated Deployment

### Before (Manual)

```bash
# SSH into server
ssh saus@nanopi-r5c-arm64

# Pull and deploy
cd ~/workspace/chicago-garden-planner
git pull
./scripts/deploy.sh
```

**Time:** ~5-10 minutes
**Requires:** SSH access

### After (Automated)

```bash
# From anywhere (your Mac, laptop, etc.)
./scripts/release.sh 1.0.0 "New features"
```

**Time:** ~3-5 minutes (automated)
**Requires:** Git push access only

## Next Steps

1. ✅ Set up the runner (you're doing this now!)
2. ✅ Test with a release: `./scripts/release.sh 1.0.0`
3. ✅ Monitor the deployment in GitHub Actions
4. ✅ Verify the site is updated
5. ✅ Set up notifications (optional - see GitHub Settings > Notifications)

## Additional Resources

- [GitHub Actions Self-Hosted Runners Docs](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Securing Self-Hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/about-self-hosted-runners#self-hosted-runner-security)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
