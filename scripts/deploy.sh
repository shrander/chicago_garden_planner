#!/bin/bash

# Deployment script for Chicago Garden Planner with Traefik
# Run this on your server to deploy the application

set -e  # Exit on error

echo "🌱 Deploying Chicago Garden Planner with Traefik..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file from .env.example and configure it."
    exit 1
fi

# Check if proxy network exists
if ! docker network ls | grep -q "proxy"; then
    echo "📡 Creating proxy network for Traefik..."
    docker network create proxy
fi

# Pull latest changes (if using git on server)
if [ -d .git ]; then
    echo "📥 Pulling latest changes..."
    git pull origin main
fi

# Build and start containers
echo "🐳 Building and starting Docker containers..."
docker-compose build --no-cache
docker-compose down
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run migrations
echo "🔄 Running database migrations..."
docker-compose exec -T web python manage.py migrate --noinput

# Collect static files
echo "📦 Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput

# Create default data (optional - uncomment if needed)
# echo "📚 Populating default plants..."
# docker-compose exec -T web python manage.py populate_default_plants

# Check container status
echo "✅ Checking container status..."
docker-compose ps

# Show logs
echo "📋 Recent logs:"
docker-compose logs --tail=30

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Your application should be accessible via Traefik at:"
echo "  https://\${DOMAIN_NAME} (configured in .env)"
echo ""
echo "Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Restart: docker-compose restart"
echo "  Stop: docker-compose down"
echo "  Shell: docker-compose exec web python manage.py shell"
echo ""
echo "Note: Ensure Traefik is running and configured with:"
echo "  - External 'proxy' network"
echo "  - 'websecure' entrypoint (port 443)"
echo "  - Certificate resolver 'myresolver'"
