#!/bin/bash

# Release script - Create version tag and trigger deployment
# Usage: ./scripts/release.sh <version> [message]
# Example: ./scripts/release.sh 1.0.0 "Initial release"
# Example: ./scripts/release.sh 1.0.1

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if version is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Version number required${NC}"
    echo ""
    echo "Usage: ./scripts/release.sh <version> [message]"
    echo ""
    echo "Examples:"
    echo "  ./scripts/release.sh 1.0.0 \"Initial production release\""
    echo "  ./scripts/release.sh 1.0.1 \"Bug fixes\""
    echo "  ./scripts/release.sh 1.1.0 \"New features\""
    echo ""
    exit 1
fi

VERSION=$1
MESSAGE=${2:-"Release version $VERSION"}

# Add 'v' prefix if not present
if [[ ! $VERSION =~ ^v ]]; then
    VERSION="v$VERSION"
fi

# Validate version format (vX.Y.Z)
if [[ ! $VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}Error: Invalid version format${NC}"
    echo "Version must be in format: v1.0.0 (or just 1.0.0)"
    exit 1
fi

# Check if tag already exists
if git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo -e "${RED}Error: Tag $VERSION already exists${NC}"
    echo ""
    echo "Existing tags:"
    git tag -l "v*" | tail -5
    exit 1
fi

# Ensure we're on main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}Warning: You are not on the main branch (current: $CURRENT_BRANCH)${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}Warning: You have uncommitted changes${NC}"
    git status --short
    echo ""
    read -p "Commit changes before creating tag? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        git add -A
        read -p "Enter commit message: " COMMIT_MSG
        git commit -m "$COMMIT_MSG"
    fi
fi

# Pull latest changes
echo -e "${GREEN}📥 Pulling latest changes...${NC}"
git pull origin $CURRENT_BRANCH

# Show recent commits
echo ""
echo -e "${GREEN}📋 Recent commits since last tag:${NC}"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
    git log $LAST_TAG..HEAD --oneline --no-decorate | head -10
else
    git log --oneline --no-decorate | head -10
fi

echo ""
echo -e "${GREEN}🏷️  Creating tag: $VERSION${NC}"
echo -e "${GREEN}📝 Message: $MESSAGE${NC}"
echo ""
read -p "Proceed with release? (Y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Create annotated tag
git tag -a "$VERSION" -m "$MESSAGE"

# Push tag to remote
echo -e "${GREEN}🚀 Pushing tag to remote...${NC}"
git push origin "$VERSION"

echo ""
echo -e "${GREEN}✅ Release $VERSION created successfully!${NC}"
echo ""
echo "🎉 Deployment will start automatically via GitHub Actions"
echo ""
echo "View deployment progress:"
echo "  https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
echo ""
echo "Recent tags:"
git tag -l "v*" | tail -5
echo ""
