#!/bin/bash

# Azure App Service startup script for Django
echo "🚀 Starting Decipherworld Django application on Azure..."

# Set Django settings module for Azure
export DJANGO_SETTINGS_MODULE=decipherworld.settings.azure

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --settings=decipherworld.settings.azure

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --settings=decipherworld.settings.azure

# Create superuser if needed (optional - only for first deployment)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "👤 Creating superuser..."
    python manage.py shell --settings=decipherworld.settings.azure << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', '${ADMIN_EMAIL:-admin@decipherworld.com}', '${ADMIN_PASSWORD:-changeme123}')
    print('Superuser created successfully!')
else:
    print('Superuser already exists.')
EOF
fi

# Start Gunicorn server
echo "🌐 Starting Gunicorn server..."
exec gunicorn decipherworld.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WORKERS:-2} \
    --timeout ${TIMEOUT:-120} \
    --keep-alive ${KEEP_ALIVE:-2} \
    --max-requests ${MAX_REQUESTS:-1000} \
    --max-requests-jitter ${MAX_REQUESTS_JITTER:-100} \
    --access-logfile - \
    --error-logfile -