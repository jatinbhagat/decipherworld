"""
Emergency timeout fixes for production
Add these settings to your production.py file
"""

# Database connection optimization
DATABASES_TIMEOUT_FIX = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'connect_timeout': 30,        # 30 second connection timeout
            'options': '-c statement_timeout=30000 -c idle_in_transaction_session_timeout=30000'
        },
        'CONN_MAX_AGE': 300,    # Keep connections for 5 minutes (reduced from 600)
        'CONN_HEALTH_CHECKS': True,  # Enable connection health checks
    }
}

# Request handling timeouts
TIMEOUT_MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # Compress responses early
    'core.middleware.TimeoutMiddleware',      # Monitor request times
    'core.middleware.HealthCheckMiddleware',  # Fast health checks
    # ... rest of your middleware
]

# Static files optimization
STATIC_FILES_OPTIMIZATION = {
    'STATICFILES_STORAGE': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    'WHITENOISE_USE_FINDERS': True,
    'WHITENOISE_AUTOREFRESH': False,  # Disable in production
    'WHITENOISE_SKIP_COMPRESS_EXTENSIONS': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br'],
}

# Request size limits to prevent large uploads causing timeouts
REQUEST_LIMITS = {
    'DATA_UPLOAD_MAX_MEMORY_SIZE': 5242880,  # 5MB
    'FILE_UPLOAD_MAX_MEMORY_SIZE': 5242880,  # 5MB
    'DATA_UPLOAD_MAX_NUMBER_FIELDS': 1000,
}

# Session optimization
SESSION_OPTIMIZATION = {
    'SESSION_ENGINE': 'django.contrib.sessions.backends.cached_db',
    'SESSION_CACHE_ALIAS': 'default',
    'SESSION_COOKIE_AGE': 1800,  # 30 minutes
    'SESSION_EXPIRE_AT_BROWSER_CLOSE': True,
}

# Caching to reduce database load
CACHES_CONFIG = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Logging configuration for debugging timeouts
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'WARNING',  # Only log slow queries
            'handlers': ['console'],
        },
        'core.middleware': {
            'level': 'WARNING',
            'handlers': ['console'],
        },
    },
}

# Security settings that might affect timeouts
SECURITY_SETTINGS = {
    'SECURE_CONTENT_TYPE_NOSNIFF': True,
    'SECURE_BROWSER_XSS_FILTER': True,
    'X_FRAME_OPTIONS': 'DENY',
    'SECURE_HSTS_SECONDS': 31536000,  # 1 year
    'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
}

# Azure-specific optimizations
AZURE_OPTIMIZATIONS = {
    'ALLOWED_HOSTS': [
        'decipherworld-app.azurewebsites.net',
        'decipherworld.com',
        '*.azurewebsites.net',
    ],
    'USE_TZ': True,
    'TIME_ZONE': 'UTC',
}

# Emergency settings to apply immediately
EMERGENCY_SETTINGS = {
    **REQUEST_LIMITS,
    **SESSION_OPTIMIZATION,
    **AZURE_OPTIMIZATIONS,
    'DEBUG': False,
    'ALLOWED_HOSTS': ['*'],  # Temporary - restrict later
}