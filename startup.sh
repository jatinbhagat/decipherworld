#!/bin/bash

# Azure App Service startup script for Django
echo "🚀 Starting Decipherworld Django application..."

# Set Django settings module for Azure
export DJANGO_SETTINGS_MODULE=decipherworld.settings.production

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations (essential for Django)
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput --settings=decipherworld.settings.production

# Fix missing ConstitutionOption columns (production fix)
echo "🔧 Fixing Constitution game columns..."
python manage.py fix_constitution_columns --settings=decipherworld.settings.production

# Collect static files (needed for Django admin and CSS)
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --settings=decipherworld.settings.production

# Start Gunicorn server
echo "🌐 Starting Gunicorn server..."
exec gunicorn decipherworld.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WORKERS:-2} \
    --timeout ${TIMEOUT:-60} \
    --access-logfile - \
    --error-logfile -