#!/bin/bash

# SSL/TLS Certificate Setup using Let's Encrypt
# Run this script on your server after initial deployment

set -e

echo "🔒 Setting up SSL/TLS certificates with Let's Encrypt..."

# Check if domain is provided
if [ -z "$1" ]; then
    echo "Usage: ./setup-ssl.sh your-domain.com [your-email@example.com]"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"admin@$DOMAIN"}

echo "Domain: $DOMAIN"
echo "Email: $EMAIL"

# Obtain certificate
echo "📜 Obtaining SSL certificate..."
docker-compose run --rm certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# Update nginx configuration
echo "🔧 Updating nginx configuration..."
echo "Please uncomment the HTTPS server block in nginx/conf.d/app.conf"
echo "and update 'your-domain.com' with '$DOMAIN'"
echo ""
echo "Then run: docker-compose restart nginx"
echo ""
echo "Also update your .env file:"
echo "  ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN"
echo "  SECURE_SSL_REDIRECT=True"
echo "  SESSION_COOKIE_SECURE=True"
echo "  CSRF_COOKIE_SECURE=True"
echo "  SECURE_HSTS_SECONDS=31536000"
echo ""
echo "✅ SSL certificate obtained successfully!"
echo "Certificate will auto-renew via certbot container."
