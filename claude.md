# CLAUDE.md – Django + Azure Website Development Guide

## 1. Project Setup
Prompt:  
Generate step-by-step commands to initialize a Django project called `decipherworld`, add a `core` app, and set up for deployment on Microsoft Azure App Service with Azure PostgreSQL. Assume a fresh environment.

---

## 2. Django Project Structure
Prompt:  
Generate the recommended Django project folder structure for a site with landing pages, signup/login, course listings, and a contact/demo form, using templates and class-based views. Use mobile-first design conventions.

---

## 3. Models & Django ORM
Prompt:  
Generate Django models for Courses, Schools, Teachers, DemoRequests. Use Django's built-in ORM and authentication system with PostgreSQL database.

---

## 4. URLs, Views & Template Setup
Prompt:  
Generate example Django URLs, views (CBV where possible), and templates for:  
- Homepage displaying product highlights and CTAs  
- Courses page listing all courses dynamically  
- Teacher/Admin signup/login with Django auth  
- Contact/demo request form  
- Success page/messages

---

## 5. HTML & Tailwind CSS
Prompt:  
Generate responsive, minimal HTML + Tailwind CSS templates for each section (hero, mission, courses, product blurbs, signup, contact form, footer), inserting previously generated site copy in the appropriate places.

---

## 6. Demo Request Form Logic
Prompt:  
Generate Django form and view logic for submitting demo/contact requests, saving to PostgreSQL using Django ORM, with error handling and success feedback on UI.

---

## 7. Azure Deployment
Prompt:  
Generate Azure App Service deployment configuration with proper static file serving, environment variables, and GitHub Actions workflow for CI/CD.

---

## 8. Instructions for Using Generated Content
Prompt:  
Show how to map the content (site copy, emails, etc) you generated earlier into Django templates, context, and, optionally, translation/lookups for maintainability.

---

## 9. Azure Deployment Configuration

### Required Django Project Structure:
```
decipherworld/
├── manage.py                   # Django management script
├── decipherworld/             # Main project package  
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py           # Base settings
│   │   ├── local.py          # Local development
│   │   ├── production.py     # Production overrides
│   │   └── azure.py          # Azure-specific settings
│   ├── urls.py
│   └── wsgi.py
├── core/                      # Main app
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── templates/
├── static/
├── requirements.txt
├── startup.sh                 # Azure startup script
└── .github/workflows/
    └── azure-webapps-python.yml
```

### Essential Files:
- `manage.py`: Django management commands
- `decipherworld/settings/base.py`: Common settings
- `decipherworld/settings/production.py`: Production overrides
- `decipherworld/settings/azure.py`: Azure-specific configuration
- `startup.sh`: Azure App Service startup script
- Proper `INSTALLED_APPS` and middleware configuration
- Environment variables in Azure App Service configuration

### Common Deployment Errors:
1. Missing `manage.py` - prevents Django commands
2. Incorrect `DJANGO_SETTINGS_MODULE` path
3. Missing `BASE_DIR` in settings
4. **Database connection issues** - Most common error
5. Static files configuration errors
6. Azure App Service startup configuration

### Azure PostgreSQL Database Configuration:

**CRITICAL**: Get the correct connection details from Azure Portal:

**Step 1: Find Connection Details in Azure Portal**
1. Go to Azure Portal → PostgreSQL flexible servers
2. Select your PostgreSQL server
3. Go to "Settings" → "Connection strings"
4. Copy the connection details

**Step 2: Set Environment Variables in Azure App Service**

✅ **METHOD 1 - CONNECTION STRING (Recommended):**
```
DATABASE_URL = postgresql://decipheradmin:[YOUR-PASSWORD]@decipherworld-db-server-ci01.postgres.database.azure.com:5432/decipherworld?sslmode=require
```

✅ **METHOD 2 - Individual Parameters:**
```
DB_HOST = decipherworld-db-server-ci01.postgres.database.azure.com
DB_NAME = decipherworld
DB_USER = decipheradmin
DB_PASSWORD = your_actual_password
DB_PORT = 5432
```

**IMPORTANT NOTES:**
- **SSL Required**: Azure PostgreSQL requires SSL connections
- **Port 5432**: Standard PostgreSQL port for Azure
- **Firewall Rules**: Ensure Azure App Service has access to PostgreSQL server
- **Connection Pooling**: Configure appropriately for production workloads

**Azure Environment Variables Setup:**
```bash
# Set in Azure App Service Configuration
az webapp config appsettings set --resource-group rg-decipherworld-prod --name decipherworld-app --settings \
    DJANGO_SETTINGS_MODULE=decipherworld.settings.production \
    DATABASE_URL="postgresql://decipheradmin:PASSWORD@HOST:5432/decipherworld?sslmode=require" \
    SECRET_KEY="your-secret-key" \
    DEBUG=False
```

### Azure Resources Required:
1. **Resource Group**: `rg-decipherworld-prod`
2. **App Service Plan**: `decipherworld-app-plan` (Linux)
3. **Web App**: `decipherworld-app`
4. **PostgreSQL Server**: `decipherworld-db-server-ci01`
5. **PostgreSQL Database**: `decipherworld`

### Template Structure:
```
decipherworld/
├── templates/
│   ├── base.html
│   ├── home/
│   │   ├── index.html          # Hero section + homepage content
│   │   ├── about.html          # Mission statement
│   │   ├── courses.html        # Course offerings grid
│   │   ├── teachers.html       # For Teachers & Administrators
│   │   ├── contact.html        # Contact & Demo form
│   │   └── coming-soon.html    # Future feature teaser
│   ├── includes/
│   │   ├── header.html
│   │   ├── footer.html
│   │   └── nav.html
│   └── emails/
│       └── onboarding.html     # Welcome email template
```

### Azure-Specific Configuration:
- **Static Files**: Configure Azure Blob Storage or use WhiteNoise
- **Logging**: Use Azure Application Insights
- **SSL/HTTPS**: Enabled by default on Azure App Service
- **Custom Domain**: Configure DNS and SSL certificates
- **Scaling**: Configure auto-scaling rules based on demand

### Development vs Production:
- **Local Development**: Can use Azure PostgreSQL or SQLite
- **Production**: Always use Azure PostgreSQL with SSL
- **Environment Variables**: Use `.env` locally, Azure App Service settings in production
- **Static Files**: WhiteNoise for simplicity, Azure Storage for high-traffic sites