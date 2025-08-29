from .base import *
from decouple import config
import os

# Override base settings for production
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-temp-key-change-in-production')

ALLOWED_HOSTS = [
    'decipherworld.onrender.com',  # Your Render subdomain
    'www.decipherworld.com',       # Your custom domain (if any)
    'decipherworld.com',
    '.onrender.com',  # Allow all Render subdomains during deployment
]

# Database Configuration (Supabase PostgreSQL)
def get_db_host():
    """Extract hostname from DB_HOST, removing protocol if present"""
    host = config('DB_HOST')
    # Remove https:// or http:// if present
    if host.startswith('https://'):
        host = host.replace('https://', '')
    elif host.startswith('http://'):
        host = host.replace('http://', '')
    # Remove trailing slash if present
    host = host.rstrip('/')
    
    # If using direct connection host (db.xxx.supabase.co), convert to correct pooler
    if host.startswith('db.') and '.supabase.co' in host:
        # Convert to the actual pooler host for your region
        pooler_host = "aws-1-ap-south-1.pooler.supabase.com"
        print(f"Converting direct host {host} to pooler: {pooler_host}")
        return pooler_host
    
    return host

# Database Configuration - Supabase with Connection Pooling
import dj_database_url
DATABASE_URL = config('DATABASE_URL', default=None)
DIRECT_URL = config('DIRECT_URL', default=None)

if DATABASE_URL:
    # Use connection pooling for main database operations (port 6543)
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
    }
    
    # Override port if using pooling (should be 6543 for connection pooling)
    if 'pgbouncer=true' in DATABASE_URL:
        DATABASES['default']['PORT'] = 6543
        print("Using Supabase connection pooling (port 6543)")
    
elif DIRECT_URL:
    # Use direct connection (port 5432)
    DATABASES = {
        'default': dj_database_url.parse(DIRECT_URL, conn_max_age=600, ssl_require=True)
    }
    print("Using Supabase direct connection (port 5432)")
    
else:
    # Fallback to individual environment variables
    db_port = config('DB_PORT', default='6543')  # Default to pooling port
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='postgres'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': get_db_host(),
            'PORT': db_port,
            'OPTIONS': {
                'sslmode': 'require',
                'connect_timeout': 60,
                'application_name': 'django_decipherworld',
            },
            'CONN_MAX_AGE': 600,
        }
    }
    print(f"Using fallback connection to {get_db_host()}:{db_port}")

# For migrations, we might need direct connection (port 5432)
# This will be used if DIRECT_URL is provided and we're running migrations

# Supabase Configuration
SUPABASE_URL = config('SUPABASE_URL')
SUPABASE_KEY = config('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = config('SUPABASE_SERVICE_KEY', default='')

# Static Files Configuration
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Use WhiteNoise for static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CORS Settings (if using frontend frameworks)
CORS_ALLOWED_ORIGINS = [
    "https://decipherworld.onrender.com",
    "https://www.decipherworld.com",
]

# Logging
LOGGING = {
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
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

# Debug database connection (only in production for troubleshooting)
if not DEBUG:
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Database config - HOST: {get_db_host()}, NAME: {config('DB_NAME')}, USER: {config('DB_USER')}, PORT: {config('DB_PORT', default='5432')}")