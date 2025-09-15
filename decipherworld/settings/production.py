"""
Production settings for decipherworld project.
Extends base settings with production-specific configurations.
"""

from .base import *
from decouple import config

# Production overrides
DEBUG = False
SECRET_KEY = config('SECRET_KEY')

# Production hosts
ALLOWED_HOSTS = [
    'decipherworld-app.azurewebsites.net',
    'www.decipherworld.com',
    'decipherworld.com',
    '.azurewebsites.net',  # Allow all Azure App Service domains
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
CSRF_COOKIE_HTTPONLY = True
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