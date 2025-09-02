#!/bin/bash

# Simplified Azure App Service startup script
echo "🚀 Starting Decipherworld Django application..."

# Set Django settings module for Azure
export DJANGO_SETTINGS_MODULE=decipherworld.settings.azure

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Start Gunicorn server (skip migrations/collectstatic for now)
echo "🌐 Starting Gunicorn server..."
exec gunicorn decipherworld.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WORKERS:-2} \
    --timeout ${TIMEOUT:-60} \
    --access-logfile - \
    --error-logfile -