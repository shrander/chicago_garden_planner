#!/bin/bash

# GitHub Actions Self-Hosted Runner Setup Script for NanoPi
# This script installs and configures a GitHub Actions runner on your server
# so GitHub can trigger deployments without SSH access from the internet.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}GitHub Actions Self-Hosted Runner Setup${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ Please do not run this script as root${NC}"
    echo "The runner should be installed as your regular user (saus)"
    exit 1
fi

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    RUNNER_ARCH="arm64"
elif [ "$ARCH" = "x86_64" ]; then
    RUNNER_ARCH="x64"
else
    echo -e "${RED}❌ Unsupported architecture: $ARCH${NC}"
    exit 1
fi

echo -e "${BLUE}Detected architecture: $RUNNER_ARCH${NC}"
echo ""

# Get repository information
echo -e "${YELLOW}📋 Repository Information${NC}"
echo "Please provide your GitHub repository details:"
echo ""
read -p "GitHub username/organization: " GITHUB_OWNER
read -p "Repository name (chicago_garden_planner): " GITHUB_REPO
GITHUB_REPO=${GITHUB_REPO:-chicago_garden_planner}

echo ""
echo -e "${YELLOW}🔑 GitHub Personal Access Token${NC}"
echo "You need a GitHub Personal Access Token (PAT) with 'repo' and 'workflow' scopes."
echo "Create one at: https://github.com/settings/tokens/new"
echo ""
read -sp "Enter your GitHub PAT: " GITHUB_TOKEN
echo ""
echo ""

# Create runner directory
RUNNER_DIR="$HOME/actions-runner"
echo -e "${BLUE}📁 Creating runner directory: $RUNNER_DIR${NC}"
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

# Get latest runner version
echo -e "${BLUE}🔍 Fetching latest runner version...${NC}"
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | grep -oP '"tag_name": "v\K(.*)(?=")')
if [ -z "$RUNNER_VERSION" ]; then
    echo -e "${RED}❌ Failed to fetch runner version${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Latest version: $RUNNER_VERSION${NC}"

# Download runner
RUNNER_FILE="actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"
RUNNER_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_FILE}"

echo -e "${BLUE}⬇️  Downloading runner...${NC}"
if [ -f "$RUNNER_FILE" ]; then
    echo -e "${YELLOW}Runner package already exists, skipping download${NC}"
else
    curl -o "$RUNNER_FILE" -L "$RUNNER_URL"
fi

# Extract runner
echo -e "${BLUE}📦 Extracting runner...${NC}"
tar xzf "$RUNNER_FILE"

# Get registration token
echo -e "${BLUE}🔑 Getting registration token from GitHub...${NC}"
REGISTRATION_TOKEN=$(curl -s -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/runners/registration-token" \
    | grep -oP '"token": "\K(.*)(?=")')

if [ -z "$REGISTRATION_TOKEN" ]; then
    echo -e "${RED}❌ Failed to get registration token${NC}"
    echo "Please check:"
    echo "  1. Your PAT has 'repo' and 'workflow' scopes"
    echo "  2. Repository name is correct: ${GITHUB_OWNER}/${GITHUB_REPO}"
    exit 1
fi

echo -e "${GREEN}✓ Registration token received${NC}"

# Configure runner
echo ""
echo -e "${BLUE}⚙️  Configuring runner...${NC}"
./config.sh \
    --url "https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}" \
    --token "$REGISTRATION_TOKEN" \
    --name "nanopi-$(hostname)" \
    --work "_work" \
    --labels "self-hosted,Linux,ARM64,production" \
    --unattended \
    --replace

# Install as a service
echo ""
echo -e "${BLUE}🔧 Installing runner as a systemd service...${NC}"
sudo ./svc.sh install $USER

# Start the service
echo -e "${BLUE}▶️  Starting runner service...${NC}"
sudo ./svc.sh start

# Check status
echo ""
echo -e "${BLUE}🔍 Checking runner status...${NC}"
sudo ./svc.sh status

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ GitHub Actions Runner Setup Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${YELLOW}Runner Details:${NC}"
echo "  Name: nanopi-$(hostname)"
echo "  Repository: ${GITHUB_OWNER}/${GITHUB_REPO}"
echo "  Directory: $RUNNER_DIR"
echo "  Labels: self-hosted, Linux, ARM64, production"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo "  Check status:  sudo $RUNNER_DIR/svc.sh status"
echo "  Stop runner:   sudo $RUNNER_DIR/svc.sh stop"
echo "  Start runner:  sudo $RUNNER_DIR/svc.sh start"
echo "  Restart:       sudo $RUNNER_DIR/svc.sh restart"
echo "  View logs:     journalctl -u actions.runner.* -f"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "  1. Verify runner appears at: https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/settings/actions/runners"
echo "  2. Push a tag to test deployment: ./scripts/release.sh 1.0.0"
echo "  3. Monitor deployment: https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/actions"
echo ""
