# Azure Monitoring & Alerting Setup for DecipherWorld

## 🚨 Critical Production Monitoring Setup

### 1. Azure Application Insights Setup

#### Enable Application Insights for App Service
```bash
# Enable Application Insights for your App Service
az monitor app-insights component create \
    --app decipherworld-insights \
    --location eastus \
    --resource-group rg-decipherworld-prod \
    --application-type web

# Get the instrumentation key
az monitor app-insights component show \
    --app decipherworld-insights \
    --resource-group rg-decipherworld-prod \
    --query instrumentationKey -o tsv

# Link App Service to Application Insights
az webapp config appsettings set \
    --name decipherworld-app \
    --resource-group rg-decipherworld-prod \
    --settings APPINSIGHTS_INSTRUMENTATIONKEY=<YOUR_INSTRUMENTATION_KEY>
```

#### Add to App Service Configuration
```bash
az webapp config appsettings set \
    --name decipherworld-app \
    --resource-group rg-decipherworld-prod \
    --settings \
    APPINSIGHTS_INSTRUMENTATIONKEY=<YOUR_KEY> \
    APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=<YOUR_KEY>" \
    ApplicationInsightsAgent_EXTENSION_VERSION=~3
```

### 2. Availability Tests (Ping Tests)

#### Create Availability Test
```bash
# Create availability test to check if website is up
az monitor app-insights web-test create \
    --resource-group rg-decipherworld-prod \
    --component decipherworld-insights \
    --web-test-name "DecipherWorld Homepage Ping" \
    --web-test-kind ping \
    --locations "East US" "West US" "Central India" \
    --frequency 300 \
    --timeout 30 \
    --url "https://decipherworld-app.azurewebsites.net/" \
    --enabled true
```

### 3. Critical Alerts Setup

#### 1. Website Down Alert
```bash
# Alert when website is down
az monitor metrics alert create \
    --name "DecipherWorld Website Down" \
    --resource-group rg-decipherworld-prod \
    --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/rg-decipherworld-prod/providers/Microsoft.Web/sites/decipherworld-app \
    --condition "count availabilityResults/availabilityPercentage < 95" \
    --window-size 5m \
    --evaluation-frequency 1m \
    --severity 0 \
    --description "Website availability dropped below 95%" \
    --action-group-ids /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/rg-decipherworld-prod/providers/microsoft.insights/actionGroups/DecipherWorldAlerts
```

#### 2. High Response Time Alert
```bash
# Alert when response time is too high
az monitor metrics alert create \
    --name "DecipherWorld High Response Time" \
    --resource-group rg-decipherworld-prod \
    --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/rg-decipherworld-prod/providers/Microsoft.Web/sites/decipherworld-app \
    --condition "avg requests/duration > 5000" \
    --window-size 5m \
    --evaluation-frequency 1m \
    --severity 1 \
    --description "Average response time above 5 seconds"
```

#### 3. High Error Rate Alert
```bash
# Alert when error rate is high
az monitor metrics alert create \
    --name "DecipherWorld High Error Rate" \
    --resource-group rg-decipherworld-prod \
    --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/rg-decipherworld-prod/providers/Microsoft.Web/sites/decipherworld-app \
    --condition "count requests/failed > 10" \
    --window-size 5m \
    --evaluation-frequency 1m \
    --severity 1 \
    --description "More than 10 failed requests in 5 minutes"
```

### 4. Action Groups for Notifications

#### Create Action Group for Alerts
```bash
# Create action group for email notifications
az monitor action-group create \
    --name DecipherWorldAlerts \
    --resource-group rg-decipherworld-prod \
    --short-name DWAlerts \
    --email-receivers \
        name=admin \
        email-address=your-email@domain.com \
        use-common-schema=true
```

### 5. Custom Health Check Endpoint

Add to your Django app for better monitoring:

```python
# In core/views.py
from django.http import JsonResponse
from django.db import connection
import time

def health_check(request):
    """Comprehensive health check endpoint for monitoring"""
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    try:
        # Database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
    
    # Response time check
    response_time = (time.time() - start_time) * 1000
    health_status["response_time_ms"] = response_time
    
    if response_time > 2000:  # More than 2 seconds
        health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] in ["healthy", "degraded"] else 503
    return JsonResponse(health_status, status=status_code)

# Add URL pattern
# In core/urls.py: path('health/', views.health_check, name='health_check'),
```

### 6. Log Analytics Queries

#### Check for Common Issues
```kusto
// Failed requests in last 24 hours
requests
| where timestamp > ago(24h)
| where success == false
| summarize FailedRequests = count() by bin(timestamp, 1h)
| render timechart

// Slow requests
requests
| where timestamp > ago(24h)
| where duration > 5000  // Slower than 5 seconds
| project timestamp, name, url, duration, resultCode
| order by duration desc

// Exception tracking
exceptions
| where timestamp > ago(24h)
| summarize ExceptionCount = count() by type, outerMessage
| order by ExceptionCount desc
```

### 7. Dashboard Creation

#### Create Custom Dashboard
```bash
# Export dashboard template
az portal dashboard create \
    --resource-group rg-decipherworld-prod \
    --name "DecipherWorld Monitoring Dashboard" \
    --input-path dashboard-template.json
```

### 8. Immediate Actions Required

1. **Enable Application Insights** (5 min setup)
2. **Create availability tests** (Monitor from multiple regions)
3. **Set up critical alerts** (Website down, high errors)
4. **Add email notifications** (Get notified immediately)
5. **Deploy health check endpoint** (Better monitoring)

### 9. Monitoring Checklist

- [ ] Application Insights enabled
- [ ] Availability tests configured (3+ regions)
- [ ] Website down alert created
- [ ] High error rate alert created
- [ ] High response time alert created
- [ ] Email notifications configured
- [ ] Health check endpoint deployed
- [ ] Custom dashboard created
- [ ] Log analytics queries saved

### 10. Cost Optimization

- Standard tier Application Insights: ~$2.30/GB
- Availability tests: ~$1/test/month
- Alerts: Free (first 1000 alerts/month)
- Total estimated cost: $10-20/month for comprehensive monitoring