# 🚨 504 Gateway Timeout Emergency Response Plan

## Immediate Actions Required (Execute in Order)

### 1. **Check Current App Service Status** (2 minutes)
```bash
# Check App Service health
az webapp show --name decipherworld-app --resource-group rg-decipherworld-prod --query "state"

# Check App Service logs immediately
az webapp log show --name decipherworld-app --resource-group rg-decipherworld-prod --logs application

# Check metrics
az monitor metrics list --resource /subscriptions/YOUR-SUB/resourceGroups/rg-decipherworld-prod/providers/Microsoft.Web/sites/decipherworld-app --metric "CpuTime,MemoryWorkingSet,Requests,Http5xx" --interval PT1M
```

### 2. **Most Common Causes of 504 in Azure App Service**

#### **A. Database Connection Timeout (Most Likely)**
- PostgreSQL connections hanging
- Too many concurrent connections
- Slow queries blocking the app

#### **B. App Service Cold Start**
- App goes to sleep after inactivity
- First request after sleep takes 60+ seconds

#### **C. Resource Exhaustion**
- CPU/Memory limits reached
- Too many concurrent requests

#### **D. Dependency Timeouts**
- External API calls timing out
- Static file loading issues

### 3. **Immediate Emergency Fixes**

#### **Fix A: Force App Service Restart**
```bash
# Restart the app service immediately
az webapp restart --name decipherworld-app --resource-group rg-decipherworld-prod

# This often resolves stuck processes
```

#### **Fix B: Scale Up Temporarily**
```bash
# Scale up to higher tier temporarily for more resources
az appservice plan update --name your-plan-name --resource-group rg-decipherworld-prod --sku P1V2

# Or scale out (more instances)
az webapp update --name decipherworld-app --resource-group rg-decipherworld-prod --number-of-workers 2
```

#### **Fix C: Enable Always On**
```bash
# Prevent cold starts
az webapp config set --name decipherworld-app --resource-group rg-decipherworld-prod --always-on true
```

### 4. **Database Connection Pool Fix**

Add to `settings/production.py`:
```python
# Database connection optimization
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'connect_timeout': 30,        # 30 second connection timeout
            'options': '-c statement_timeout=30000'  # 30 second query timeout
        },
        'CONN_MAX_AGE': 600,    # Keep connections for 10 minutes
    }
}

# Connection pooling
DATABASE_POOL_CLASS = 'django_db_geventpool.backends.postgresql'
DATABASE_POOL_ARGS = {
    'max_connections': 20,    # Limit concurrent connections
    'stale_timeout': 300,     # Close stale connections after 5 minutes
}
```

### 5. **Request Timeout Configuration**

Add timeout middleware to handle long requests:
```python
# In core/middleware.py
import time
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

class TimeoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            if duration > 25:  # Log slow requests
                print(f"SLOW REQUEST: {request.path} took {duration:.2f}s")
        return response

# Add to MIDDLEWARE in settings
MIDDLEWARE = [
    'core.middleware.TimeoutMiddleware',  # Add this first
    # ... rest of middleware
]
```

### 6. **Optimize Slow Database Queries**

Check for N+1 queries and add select_related:
```python
# In views.py - Optimize queries
class HomeView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Use select_related to avoid N+1 queries
            context['courses'] = Course.objects.select_related('category').filter(is_active=True)[:4]
        except Exception as e:
            context['courses'] = []
            print(f"Database error: {e}")
        return context
```

### 7. **Static Files Optimization**

```python
# In settings/production.py
# Optimize static file serving
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# Compress responses
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # Add this early
    # ... rest of middleware
]
```

### 8. **Application Insights for Real-time Monitoring**

```bash
# Enable Application Insights immediately
az webapp config appsettings set \
    --name decipherworld-app \
    --resource-group rg-decipherworld-prod \
    --settings \
    APPINSIGHTS_INSTRUMENTATIONKEY=your-key \
    ApplicationInsightsAgent_EXTENSION_VERSION=~3 \
    XDT_MicrosoftApplicationInsights_Mode=Recommended
```

### 9. **Health Check & Proactive Monitoring**

Deploy the health check we created and monitor it:
```bash
# Test health endpoint after deployment
curl -w "Total time: %{time_total}s\n" https://decipherworld-app.azurewebsites.net/health/

# Set up availability test
az monitor app-insights web-test create \
    --resource-group rg-decipherworld-prod \
    --component decipherworld-insights \
    --web-test-name "Health Check" \
    --web-test-kind ping \
    --locations "East US" "West US" \
    --frequency 300 \
    --timeout 30 \
    --url "https://decipherworld-app.azurewebsites.net/health/" \
    --enabled true
```

### 10. **Emergency Response Checklist** (Execute Now)

#### **Immediate (Next 5 minutes):**
- [ ] Restart App Service
- [ ] Enable Always On
- [ ] Check current resource usage
- [ ] Scale up temporarily if needed

#### **Short-term (Next 30 minutes):**
- [ ] Deploy database connection optimizations
- [ ] Add timeout middleware
- [ ] Enable Application Insights
- [ ] Set up health monitoring

#### **Monitor (Next 2 hours):**
- [ ] Watch Application Insights for slow requests
- [ ] Monitor database connection pool
- [ ] Check for recurring 504 errors
- [ ] Optimize slow queries found

### 11. **Monitoring Queries for Application Insights**

```kusto
// Find slow requests causing 504s
requests
| where timestamp > ago(1h)
| where resultCode == 504 or duration > 30000
| project timestamp, name, url, duration, resultCode
| order by duration desc

// Database dependency failures
dependencies
| where timestamp > ago(1h)
| where success == false
| where dependencyType == "SQL"
| summarize count() by name, resultCode
```

### 12. **Prevention Strategy**

```python
# Add to settings/production.py
# Request timeout settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB limit
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB limit

# Session timeout
SESSION_COOKIE_AGE = 1800  # 30 minutes

# Cache configuration to reduce database load
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
        'TIMEOUT': 300,  # 5 minutes
    }
}

# Use caching in views
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # Cache for 5 minutes
def cached_view(request):
    # Expensive operations here
    pass
```

### 13. **Debugging Commands to Run Now**

```bash
# Check current app status
az webapp show --name decipherworld-app --resource-group rg-decipherworld-prod

# Check recent errors
az webapp log download --name decipherworld-app --resource-group rg-decipherworld-prod

# Monitor real-time logs
az webapp log tail --name decipherworld-app --resource-group rg-decipherworld-prod

# Check resource metrics
az monitor metrics list --resource /subscriptions/YOUR-SUB/resourceGroups/rg-decipherworld-prod/providers/Microsoft.Web/sites/decipherworld-app --metric "CpuTime" --interval PT1M
```

## **Most Likely Root Cause Based on Django Apps:**

1. **Database connection pool exhaustion** (70% probability)
2. **Cold start after inactivity** (20% probability)  
3. **Slow unoptimized queries** (10% probability)

## **Execute This Order:**
1. **Restart app service** (immediate relief)
2. **Enable Always On** (prevent cold starts)
3. **Deploy database optimizations** (fix root cause)
4. **Monitor with Application Insights** (prevent recurrence)