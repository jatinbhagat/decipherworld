#!/bin/bash

# Azure App Service runtime script for Django
echo "🚀 Starting Decipherworld Django application..."

# Set Django settings module for Azure
export DJANGO_SETTINGS_MODULE=decipherworld.settings.production

# Run database migrations (essential for Django)
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput --settings=decipherworld.settings.production || echo "⚠️ Some migrations may have conflicts, continuing..."

# Fix missing ConstitutionOption columns (production fix)
echo "🔧 Fixing Constitution game columns..."
python manage.py fix_constitution_columns --settings=decipherworld.settings.production || echo "⚠️ Constitution columns fix failed, continuing..."

# Populate learning modules for Constitution game
echo "📚 Populating Constitution game learning modules..."
python manage.py populate_learning_modules --settings=decipherworld.settings.production || echo "⚠️ Learning module population failed, skipping..."

# Create Advanced Constitution Challenge game
echo "🎓 Creating Advanced Constitution Challenge game..."
python manage.py create_advanced_constitution_game --settings=decipherworld.settings.production || echo "⚠️ Advanced game creation failed, skipping..."

# Create Advanced Constitution learning modules
echo "📖 Creating Advanced Constitution learning modules..."
python manage.py create_advanced_learning_modules --settings=decipherworld.settings.production || echo "⚠️ Advanced learning modules creation failed, skipping..."

# Collect static files (needed for Django admin and CSS)
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --settings=decipherworld.settings.production

echo "✅ Startup tasks completed. Application ready."