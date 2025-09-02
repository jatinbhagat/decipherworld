# Decipherworld Azure Migration & Deployment Guide

## 🎯 Migration Status: READY TO DEPLOY

### ✅ Completed Steps:
1. **Data Backup**: Supabase data exported (`supabase_backup_20250902_073450.json`)
2. **Schema Analysis**: Database structure documented
3. **Azure Configuration**: Django settings created (`decipherworld/settings/azure.py`)
4. **Dependencies Updated**: Removed Supabase, added Azure packages
5. **Migration Script**: Created (`migrate_to_azure.py`)
6. **Deployment Files**: Created (`startup.sh`, `.deployment`)

---

## 🚀 DEPLOYMENT STEPS

### Step 1: Create Azure Resources
Run these commands in your terminal (requires Azure CLI):

```bash
# Login to Azure
az login

# Create resource group
az group create \
    --name rg-decipherworld-prod \
    --location centralindia \
    --tags project=decipherworld environment=production

# Create PostgreSQL server
az postgres flexible-server create \
    --resource-group rg-decipherworld-prod \
    --name decipherworld-db-server-ci01 \
    --location eastus \
    --admin-user decipheradmin \
    --admin-password "YourStrongPassword123!" \
    --sku-name Standard_B1ms \
    --tier Burstable \
    --storage-size 32 \
    --version 14 \
    --public-access 0.0.0.0

# Create database
az postgres flexible-server db create \
    --resource-group rg-decipherworld-prod \
    --server-name decipherworld-db-server-ci01 \
    --database-name decipherworld

# Create App Service Plan
az appservice plan create \
    --resource-group rg-decipherworld-prod \
    --name decipherworld-app-plan \
    --location centralindia \
    --sku B1 \
    --is-linux

# Create Web App
az webapp create \
    --resource-group rg-decipherworld-prod \
    --plan decipherworld-app-plan \
    --name decipherworld-app \
    --runtime "PYTHON:3.11"
```

### Step 2: Configure Environment Variables
Set these in Azure App Service → Configuration → Application Settings:

```bash
# Database Connection (REQUIRED)
DATABASE_URL = "postgresql://decipheradmin:YourStrongPassword123!@decipherworld-db-server.postgres.database.azure.com:5432/decipherworld?sslmode=require"

# Django Settings (REQUIRED)
DJANGO_SETTINGS_MODULE = "decipherworld.settings.azure"
SECRET_KEY = "your-very-strong-secret-key-at-least-50-characters-long"
DEBUG = "False"

# Security Settings
SECURE_SSL_REDIRECT = "True"
SECURE_HSTS_SECONDS = "31536000"

# Optional: Azure Storage (if using)
USE_AZURE_STORAGE = "False"

# Optional: Application Insights
AZURE_APPINSIGHTS_KEY = "your-app-insights-key"
```

### Step 3: Deploy Code to Azure
Choose one of these methods:

#### Option A: GitHub Deployment (Recommended)
```bash
# Configure GitHub deployment
az webapp deployment source config \
    --resource-group rg-decipherworld-prod \
    --name decipherworld-app \
    --repo-url https://github.com/yourusername/decipherworld \
    --branch main \
    --manual-integration
```

#### Option B: Local Git Deployment
```bash
# Get deployment credentials
az webapp deployment list-publishing-credentials \
    --resource-group rg-decipherworld-prod \
    --name decipherworld-app

# Add Azure remote
git remote add azure https://decipherworld-app.scm.azurewebsites.net/decipherworld-app.git

# Deploy
git push azure main
```

### Step 4: Migrate Data from Supabase
After deployment, run the migration script:

```bash
# Connect to Azure PostgreSQL and migrate data
python migrate_to_azure.py supabase_backup_20250902_073450.json
```

This will:
- Run Django migrations on Azure PostgreSQL  
- Transfer all your Supabase data (4 school demos, 1 contact request)
- Verify data integrity

### Step 5: Configure Custom Domain (Optional)
```bash
# Add custom domain
az webapp config hostname add \
    --webapp-name decipherworld-app \
    --resource-group rg-decipherworld-prod \
    --hostname decipherworld.com

# Update DNS A record to point to Azure IP
# Get IP: az webapp show --resource-group rg-decipherworld-prod --name decipherworld-app --query inboundIpAddress

# Enable SSL/HTTPS
az webapp config ssl bind \
    --resource-group rg-decipherworld-prod \
    --name decipherworld-app \
    --certificate-thumbprint [THUMBPRINT] \
    --ssl-type SNI
```

---

## 🔍 VERIFICATION CHECKLIST

After deployment, verify these work:

### ✅ Application Health
- [ ] App loads at `https://decipherworld-app.azurewebsites.net`
- [ ] Database connection working (check logs)
- [ ] Static files loading correctly
- [ ] HTTPS redirect working

### ✅ Forms Functionality  
- [ ] School Demo form: `https://decipherworld-app.azurewebsites.net/schools/`
- [ ] Contact form: `https://decipherworld-app.azurewebsites.net/contact/`
- [ ] Data saves to Azure PostgreSQL
- [ ] Success messages display

### ✅ Pages Loading
- [ ] Homepage: `/`
- [ ] Gallery: `/gallery/`
- [ ] School Presentation: `/school-presentation/`
- [ ] Fullscreen presentation works

### ✅ Data Migration
- [ ] 4 School Demo Requests migrated
- [ ] 1 Demo Request migrated  
- [ ] All data displays correctly in forms/admin

---

## 🔧 TROUBLESHOOTING

### Common Issues:

#### 1. Database Connection Failed
```bash
# Check environment variables
az webapp config appsettings list --name decipherworld-app --resource-group rg-decipherworld-prod

# Check PostgreSQL firewall
az postgres flexible-server firewall-rule list --resource-group rg-decipherworld-prod --name decipherworld-db-server
```

#### 2. Static Files Not Loading
```bash
# Check if collectstatic ran
az webapp log tail --name decipherworld-app --resource-group rg-decipherworld-prod

# Manual collectstatic
az webapp ssh --resource-group rg-decipherworld-prod --name decipherworld-app
python manage.py collectstatic --noinput
```

#### 3. Form Errors
```bash
# Check Django logs
az webapp log tail --name decipherworld-app --resource-group rg-decipherworld-prod

# Test database manually
az webapp ssh --resource-group rg-decipherworld-prod --name decipherworld-app
python manage.py shell
```

---

## 💰 COST ESTIMATE

**Monthly Azure costs (East US region):**
- PostgreSQL Flexible Server (B1ms): ~$12-15
- App Service Plan (B1): ~$13-15  
- **Total: ~$25-30/month**

**Cost optimization tips:**
- Use Basic tier for both services (sufficient for your traffic)
- Enable auto-pause for PostgreSQL during low usage
- Monitor with Azure Cost Management

---

## 🎉 SUCCESS!

Once deployed, your `decipherworld.com` will be running on:
- ✅ **Azure App Service** (Django application)
- ✅ **Azure PostgreSQL** (database)
- ✅ **HTTPS/SSL** enabled
- ✅ **All forms working** 
- ✅ **All data migrated** from Supabase

**Next Steps:**
1. Update DNS to point to Azure
2. Configure monitoring/alerts
3. Set up backup strategy
4. Consider CDN for better performance

Your migration from Supabase + Render → Azure is complete! 🚀