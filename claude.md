# CLAUDE.md – Django Development & Deployment Guide

## Project Overview
DecipherWorld is a Django 4.2+ educational platform featuring:
- AI-powered learning games for students
- Teacher training tools with 5X productivity boost  
- Group collaboration scenarios
- Game-based courses (AI, Financial Literacy, Climate Change)

## Tech Stack
- **Backend**: Django + PostgreSQL
- **Frontend**: Django Templates + Tailwind CSS + DaisyUI
- **Deployment**: Azure App Service + Azure PostgreSQL
- **Static Files**: WhiteNoise

## Project Structure
```
decipherworld/
├── manage.py
├── decipherworld/settings/
│   ├── base.py           # Base configuration
│   └── production.py     # Production overrides
├── core/                 # Main app (homepage, courses)
├── games/               # Games hub and landing pages
├── robotic_buddy/       # AI learning games
├── group_learning/      # Collaborative scenarios
└── templates/           # Django templates
```

## Development Setup
```bash
# Install and configure
pip install -r requirements.txt
cp .env.example .env  # Set DATABASE_URL

# Database setup
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Azure Deployment

### Required Environment Variables
Set these in Azure App Service Configuration:
```
DJANGO_SETTINGS_MODULE = decipherworld.settings.production
SECRET_KEY = your-secret-key
DATABASE_URL = postgresql://user:pass@host:5432/db?sslmode=require
```

### Database Configuration
Azure PostgreSQL connection string format:
```
postgresql://username:password@hostname:5432/database?sslmode=require
```

### Static Files
Uses WhiteNoise for static file serving (no Azure Storage needed).

### Startup Configuration
Create `startup.sh` in project root:
```bash
#!/bin/bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn decipherworld.wsgi:application
```

### Common Issues & Solutions

1. **Database Connection Errors**
   - Verify PostgreSQL server allows Azure App Service connections
   - Check connection string format and SSL requirements
   - Ensure database exists and credentials are correct

2. **Static Files Not Loading**
   - Run `python manage.py collectstatic` during deployment
   - Verify WhiteNoise is in MIDDLEWARE
   - Check STATIC_ROOT and STATIC_URL settings

3. **Template Errors**
   - Ensure templates extend correct base template (`base.html`)
   - Check template directory paths in settings

## Key Features Implementation

### Apps Architecture
- **core**: Homepage, courses, contact forms
- **games**: Games hub with individual game landing pages  
- **robotic_buddy**: AI learning games for kids
- **group_learning**: Multi-player collaborative scenarios

### Settings Configuration
- **base.py**: Common settings, SQLite fallback for local dev
- **production.py**: Azure-specific overrides, PostgreSQL, security settings

### URL Structure
```
/                    # Homepage
/courses/           # Course listings
/teachers/          # AI training for teachers
/games/            # Games hub
/games/buddy/      # AI learning games
/learn/            # Group learning platform
```

## Deployment Checklist
- [ ] Environment variables configured in Azure
- [ ] PostgreSQL database created and accessible
- [ ] Static files collected (`collectstatic`)
- [ ] Database migrations applied
- [ ] SSL/HTTPS enabled
- [ ] Custom domain configured (if applicable)

## Monitoring
- Django logging configured for Azure
- Sitemap available at `/sitemap.xml`
- Robots.txt at `/robots.txt`
- Health checks via Django's built-in monitoring

---

*This guide focuses on essential deployment and development information for efficient platform management.*