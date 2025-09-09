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

4. **🔥 CRITICAL: 503 Service Unavailable Errors**
   - **Root Cause**: Settings module mismatch in `startup.sh`
   - **Solution**: Ensure `DJANGO_SETTINGS_MODULE=decipherworld.settings.production`
   - **Check**: Both `startup.sh` script AND Azure App Service environment variables
   - **Common After**: Code simplification that removes settings files
   - **Fix Command**: `az webapp config appsettings set --name decipherworld-app --resource-group rg-decipherworld-prod --settings DJANGO_SETTINGS_MODULE=decipherworld.settings.production`

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

## 🔒 IRON-CLAD DEPLOYMENT PROCESS

**CRITICAL: Always test locally first, then deploy to production. NO EXCEPTIONS.**

### Phase 1: Local Development & Testing (MANDATORY)

#### 1. Database Migration Safety
```bash
# Always run migrations locally first
python manage.py makemigrations --dry-run  # Check what will be created
python manage.py migrate --plan            # See migration plan
python manage.py migrate                   # Apply locally
```

#### 2. Comprehensive URL Testing (MUST PASS 100%)
```bash
# Run the URL health check (must show "READY FOR PRODUCTION")
python test_urls_simple.py

# This tests:
# ✅ All core pages return 200 (no 500 errors)
# ✅ All games pages work correctly  
# ✅ Group learning reflection page (was causing 500 error)
# ✅ SEO elements present (title, meta description, canonical)
# ✅ API endpoints functional
# ✅ 404 handling works correctly
```

#### 3. SEO & Google Search Console Validation
```bash
# Check sitemap generation
curl http://localhost:8000/sitemap.xml

# Validate structured data
# Visit Google's Rich Results Test: https://search.google.com/test/rich-results
# Test pages: localhost:8000/learn/ and localhost:8000/learn/game/1/
```

#### 4. Performance & Database Optimization
```bash
# Apply performance database indexes
python manage.py migrate group_learning 0002_add_performance_indexes

# Check for N+1 queries in logs during testing
python manage.py runserver --verbosity=2
```

### Phase 2: Production Deployment (After Local Success)

#### 1. Environment Verification
```bash
# Verify Azure environment variables
az webapp config appsettings list --name decipherworld-app --resource-group rg-decipherworld-prod

# CRITICAL: Ensure these are set:
# DJANGO_SETTINGS_MODULE=decipherworld.settings.production
# SECRET_KEY=secure-production-key
# DATABASE_URL=postgresql://...
```

#### 2. Database Migrations (Production)
```bash
# Run migrations on production (in Azure Cloud Shell)
az webapp ssh --name decipherworld-app --resource-group rg-decipherworld-prod
python manage.py migrate --settings=decipherworld.settings.production
```

#### 3. Deploy Code Changes
```bash
# Deploy to Azure App Service (your preferred method)
# Via Git, Azure DevOps, or direct deployment
```

#### 4. Post-Deployment Verification (CRITICAL)
```bash
# Test production URLs immediately after deployment
python test_urls_simple.py --url https://decipherworld.com

# Key URLs to verify manually:
# ✅ https://decipherworld.com/ (homepage)
# ✅ https://decipherworld.com/learn/session/0DWOO2/reflection/ (was 500)
# ✅ https://decipherworld.com/sitemap.xml
# ✅ https://decipherworld.com/robots.txt
```

### Phase 3: Google Search Console Monitoring

#### 1. Immediate Actions After Deployment
```bash
# Submit updated sitemap to Google Search Console
# URL: https://search.google.com/search-console

# Request re-indexing of fixed pages:
# - All group learning game pages
# - The reflection pages that had 500 errors
# - Any pages with SEO improvements
```

#### 2. Monitor for 24-48 Hours
- Check Google Search Console for new crawling errors
- Monitor Azure App Service logs for any 500 errors
- Verify all pages are being indexed correctly

### 🚨 DEPLOYMENT BLOCKERS (DO NOT DEPLOY IF):

1. **URL Health Check Fails**: `test_urls_simple.py` shows any ❌ failed URLs
2. **Database Migration Issues**: Any migration conflicts or failures locally
3. **Missing Environment Variables**: Production environment not properly configured
4. **SEO Issues**: Critical pages missing title tags, meta descriptions, or canonical URLs
5. **500 Errors in Logs**: Any 500 errors during local testing

### 🎯 Success Criteria (MUST ALL BE GREEN):

- ✅ All URLs return expected status codes (200, 404 as appropriate)  
- ✅ Group learning reflection pages work (no more 500 errors)
- ✅ Sitemap includes all important pages
- ✅ All pages have proper SEO elements (title, description, canonical)
- ✅ Database performance indexes applied
- ✅ Google Search Console shows no critical errors after 24h

### 🛠️ Emergency Rollback Process

If deployment fails:
```bash
# 1. Immediately roll back code deployment
# 2. Check Azure App Service logs for error details  
# 3. Verify database state (migrations may need rollback)
# 4. Run local URL tests to identify specific failures
# 5. Fix issues locally first, then redeploy following full process
```

---

## Original Deployment Checklist
- [ ] Phase 1: Local testing completed and passed (URL health check ✅)
- [ ] Phase 2: Environment variables configured in Azure
- [ ] Phase 2: PostgreSQL database created and accessible
- [ ] Phase 2: Database migrations applied (local first, then production)
- [ ] Phase 2: Static files collected (`collectstatic`)
- [ ] Phase 2: SSL/HTTPS enabled
- [ ] Phase 3: Sitemap submitted to Google Search Console
- [ ] Phase 3: No 500 errors in production logs
- [ ] Phase 3: All critical pages indexed by Google

## Monitoring
- Django logging configured for Azure
- Sitemap available at `/sitemap.xml`
- Robots.txt at `/robots.txt`
- Health checks via Django's built-in monitoring

---

*This guide focuses on essential deployment and development information for efficient platform management.*