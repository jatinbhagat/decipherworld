"""
Production settings for decipherworld project.
Extends base settings with production-specific configurations.
"""

from .base import *
from decouple import config

# Production overrides - temporarily enable DEBUG for error diagnosis
DEBUG = True  # TEMPORARY: Enable detailed error messages
SECRET_KEY = config('SECRET_KEY')

# Production hosts
ALLOWED_HOSTS = [
    'decipherworld-app.azurewebsites.net',
    'www.decipherworld.com',
    'decipherworld.com',
    'app.decipherworld.com',
    '.azurewebsites.net',  # Allow all Azure App Service domains
    '169.254.130.5',  # Azure internal IP
    '127.0.0.1',  # Localhost for health checks
    'localhost',
] + config('ALLOWED_HOSTS', default='', cast=lambda v: [s.strip() for s in v.split(',')] if v else [])

# Database - Production PostgreSQL
DATABASE_URL = config('DATABASE_URL', default='')
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
    }
    # Add Azure PostgreSQL specific options
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
        'connect_timeout': 60,
    }

# Production Security Settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure Cookies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # Allow form submissions to access CSRF token
CSRF_COOKIE_SAMESITE = 'Lax'

# CORS for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://decipherworld-app.azurewebsites.net",
    "https://www.decipherworld.com",
    "https://decipherworld.com",
]

# Email backend for production
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# Admin email settings for error notifications
ADMINS = [
    ('DecipherWorld Admin', config('ADMIN_EMAIL', default='jatinbhagatnew@gmail.com')),
]
MANAGERS = ADMINS

# Server email for Django to send error emails
SERVER_EMAIL = config('SERVER_EMAIL', default='noreply@decipherworld.com')
DEFAULT_FROM_EMAIL = SERVER_EMAIL

# WebSocket Channel Layers - Redis for Production
# Check for Redis URL in environment
REDIS_URL = config('REDIS_URL', default='')
if REDIS_URL:
    # Use Redis for production WebSocket persistence
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [REDIS_URL],
                "capacity": 500,  # Maximum messages to store for each channel
                "expiry": 300,    # 5 minutes before messages expire (good for Azure)
                "group_expiry": 600,  # 10 minutes for group persistence
            },
        },
    }
else:
    # Fallback to InMemory with aggressive cleanup for Azure
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
            'CONFIG': {
                "capacity": 100,  # Drastically reduced for Azure memory limits
                "expiry": 30,     # Very short expiry to prevent buildup
                "group_expiry": 60,  # Quick group cleanup
            },
        },
    }

# WebSocket specific settings for Azure App Service - Optimized for performance
WEBSOCKET_TIMEOUT = 60  # Reduced to 1 minute to prevent hanging connections
WEBSOCKET_PING_INTERVAL = 10  # More frequent pings to detect dead connections
WEBSOCKET_PING_TIMEOUT = 5   # Faster timeout to close dead connections
WEBSOCKET_MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB max message size
WEBSOCKET_CONNECT_TIMEOUT = 30  # 30 seconds to establish connection

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}