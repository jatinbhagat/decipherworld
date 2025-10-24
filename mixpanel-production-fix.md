# Mixpanel Production Issues - Diagnosis & Fix

## 🚨 Critical Issue: Mixpanel Events Not Firing

### 1. Common Causes & Solutions

#### Issue A: Content Security Policy (CSP) Blocking
**Problem**: Azure App Service might have CSP that blocks external scripts
**Solution**: Check CSP headers and add Mixpanel domains to allowlist

```python
# In settings/production.py - Add CSP configuration
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Allow Mixpanel domains
CSP_SCRIPT_SRC = [
    "'self'",
    "'unsafe-inline'",
    "https://cdn.mixpanel.com",
    "https://api.mixpanel.com",
    "https://cdn4.mxpnl.com"
]

CSP_CONNECT_SRC = [
    "'self'",
    "https://api.mixpanel.com",
    "https://decide.mixpanel.com"
]
```

#### Issue B: HTTPS Mixed Content
**Problem**: HTTP requests blocked on HTTPS site
**Solution**: Ensure all Mixpanel URLs use HTTPS

```javascript
// In base.html - Force HTTPS for Mixpanel
mixpanel.init('100436c05647bbfab884ce5304fe0b65', {
    debug: true,
    track_pageview: false,
    persistence: 'cookie',
    api_host: 'https://api.mixpanel.com',  // Force HTTPS
    secure_cookie: true,  // Use secure cookies
    cross_subdomain_cookie: false
});
```

#### Issue C: Ad Blockers and Privacy Tools
**Problem**: Browser extensions blocking Mixpanel
**Solution**: Implement fallback tracking and proxy

```javascript
// Enhanced analytics with fallback
class DecipherWorldAnalytics {
    constructor() {
        this.fallbackEvents = [];
        this.mixpanelLoaded = false;
        // ... existing code
    }

    track(eventName, properties = {}) {
        try {
            if (typeof mixpanel !== 'undefined' && mixpanel.track && typeof mixpanel.track === 'function') {
                console.log('🔥 TRACKING EVENT:', eventName, properties);
                mixpanel.track(eventName, properties);
                this.mixpanelLoaded = true;
                console.log('✅ Event tracked successfully:', eventName);
            } else {
                console.warn('⚠️ MixPanel not available, storing for retry:', eventName);
                this.fallbackEvents.push({
                    event: eventName,
                    properties: properties,
                    timestamp: new Date().toISOString()
                });
                
                // Try to send via backend as fallback
                this.sendToBackend(eventName, properties);
            }
        } catch (error) {
            console.error('❌ Error tracking event:', eventName, error);
            this.sendToBackend(eventName, properties);
        }
    }

    sendToBackend(eventName, properties) {
        // Send to Django backend as fallback
        fetch('/api/track-event/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                event: eventName,
                properties: properties
            })
        }).catch(error => {
            console.error('Backend tracking failed:', error);
        });
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}
```

### 2. Production Environment Fixes

#### Fix A: Environment Detection
```javascript
// In analytics.js - Add environment detection
getBaseProperties() {
    const baseProps = {
        user_id: this.userId,
        login_status: 'Not Logged In',
        environment: window.location.hostname.includes('azurewebsites.net') ? 'production' : 'development',
        // ... rest of properties
    };

    // Add game information if available
    const gameInfo = this.getGameInfo();
    return { ...baseProps, ...gameInfo };
}
```

#### Fix B: Debug Mode for Production
```javascript
// In base.html - Enhanced debug for production
mixpanel.init('100436c05647bbfab884ce5304fe0b65', {
    debug: true,  // Keep enabled for troubleshooting
    track_pageview: false,
    persistence: 'cookie',
    api_host: 'https://api.mixpanel.com',
    secure_cookie: true,
    cross_subdomain_cookie: false,
    ip: true,  // Track IP for geolocation
    property_blacklist: [],  // Don't blacklist any properties
    loaded: function(mixpanel) {
        console.log('✅ Mixpanel loaded successfully in production');
        console.log('Mixpanel config:', mixpanel.config);
        
        // Test event immediately
        mixpanel.track('Mixpanel Loaded', {
            environment: 'production',
            timestamp: new Date().toISOString()
        });
    },
    error: function(error) {
        console.error('❌ Mixpanel error:', error);
    }
});
```

### 3. Backend Fallback Tracking

Add backend endpoint for fallback tracking:

```python
# In core/views.py
@csrf_exempt
@require_http_methods(["POST"])
def track_event_fallback(request):
    """Fallback event tracking when frontend Mixpanel fails"""
    try:
        data = json.loads(request.body)
        event_name = data.get('event')
        properties = data.get('properties', {})
        
        # Add server-side properties
        properties.update({
            'fallback_tracking': True,
            'server_timestamp': datetime.now().isoformat(),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': get_client_ip(request)
        })
        
        # Track via backend analytics
        from .analytics import track_event
        success = track_event(event_name, properties)
        
        return JsonResponse({
            'status': 'success' if success else 'failed',
            'message': 'Event tracked via backend fallback'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# Add URL: path('api/track-event/', views.track_event_fallback, name='track_event_fallback'),
```

### 4. Immediate Production Debugging

#### Step 1: Check Browser Console
Visit https://decipherworld-app.azurewebsites.net/ and check:
1. Console errors related to Mixpanel
2. Network tab for failed requests to api.mixpanel.com
3. Application tab for cookies and local storage

#### Step 2: Test Mixpanel API Directly
```javascript
// Run this in browser console on production site
console.log('Testing Mixpanel...');
console.log('Mixpanel object:', typeof mixpanel);
if (typeof mixpanel !== 'undefined') {
    mixpanel.track('Manual Test', {test: true});
    console.log('Test event sent');
} else {
    console.error('Mixpanel not loaded');
}
```

#### Step 3: Check Network Requests
```bash
# Check if Mixpanel script loads
curl -I https://cdn4.mxpnl.com/libs/mixpanel-2-latest.min.js

# Check if API is reachable
curl -X POST https://api.mixpanel.com/track \
  -H "Content-Type: application/json" \
  -d '{"event": "test", "properties": {"token": "100436c05647bbfab884ce5304fe0b65"}}'
```

### 5. Production Deployment Checklist

- [ ] Update base.html with HTTPS Mixpanel URLs
- [ ] Add CSP headers to allow Mixpanel domains
- [ ] Deploy backend fallback endpoint
- [ ] Test health check endpoint
- [ ] Verify Mixpanel token is correct
- [ ] Check browser console for errors
- [ ] Test manual event tracking
- [ ] Monitor events in Mixpanel dashboard

### 6. Quick Fix Implementation

Most likely fixes to implement immediately:

1. **Force HTTPS in Mixpanel config**
2. **Add CSP headers for Mixpanel domains**
3. **Deploy backend fallback tracking**
4. **Test with debug mode enabled**

### 7. Monitoring Events

After fixes, monitor:
- Browser console for Mixpanel logs
- Network tab for successful API calls
- Mixpanel dashboard for incoming events
- Backend logs for fallback tracking