from .base import *
from decouple import config
import os

# Override base settings for production
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-temp-key-change-in-production')

ALLOWED_HOSTS = [
    'decipherworld-app.azurewebsites.net',  # Azure App Service
    'www.decipherworld.com',                 # Custom domain
    'decipherworld.com',
    '.azurewebsites.net',  # Allow all Azure App Service subdomains
]

# Database Configuration - Azure PostgreSQL
import dj_database_url

DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    try:
        print(f"🔍 Parsing Azure DATABASE_URL (length: {len(DATABASE_URL)} chars)")
        
        # Parse the DATABASE_URL for Azure PostgreSQL
        parsed_db = dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
        
        # Ensure NAME is set properly
        if not parsed_db.get('NAME'):
            parsed_db['NAME'] = 'decipherworld'
            print("🔧 Set database NAME to 'decipherworld'")
        
        # Add Azure-specific OPTIONS
        if 'OPTIONS' not in parsed_db:
            parsed_db['OPTIONS'] = {}
        
        parsed_db['OPTIONS'].update({
            'sslmode': 'require',
            'connect_timeout': 60,
            'application_name': 'django_decipherworld',
        })
        
        DATABASES = {
            'default': parsed_db
        }
        
        print(f"✅ Using Azure DATABASE_URL - HOST: {parsed_db.get('HOST')}, PORT: {parsed_db.get('PORT')}")
        
    except Exception as e:
        print(f"❌ Error parsing Azure DATABASE_URL: {e}")
        
        # Fallback to individual environment variables
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': config('DB_NAME', default='decipherworld'),
                'USER': config('DB_USER', default='decipheradmin'),
                'PASSWORD': config('DB_PASSWORD'),
                'HOST': config('DB_HOST', default='decipherworld-db-server-ci01.postgres.database.azure.com'),
                'PORT': config('DB_PORT', default='5432'),
                'OPTIONS': {
                    'sslmode': 'require',
                    'connect_timeout': 60,
                    'application_name': 'django_decipherworld',
                },
                'CONN_MAX_AGE': 600,
            }
        }
        print("🔧 Using Azure individual environment variables fallback")
        
else:
    # Use individual Azure environment variables
    print("🔧 Using Azure individual environment variables")
    
    try:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': config('DB_NAME', default='decipherworld'),
                'USER': config('DB_USER', default='decipheradmin'),
                'PASSWORD': config('DB_PASSWORD'),
                'HOST': config('DB_HOST', default='decipherworld-db-server-ci01.postgres.database.azure.com'),
                'PORT': config('DB_PORT', default='5432'),
                'OPTIONS': {
                    'sslmode': 'require',
                    'connect_timeout': 60,
                    'application_name': 'django_decipherworld',
                },
                'CONN_MAX_AGE': 600,
            }
        }
        
        db_config = DATABASES['default']
        print(f"✅ Azure PostgreSQL configured - HOST: {db_config['HOST']}, PORT: {db_config['PORT']}")
        
    except Exception as env_error:
        print(f"❌ Azure database configuration error: {env_error}")
        raise env_error

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

# Additional Security Settings for Production
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure Cookies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Force HTTPS for forms
CSRF_USE_SESSIONS = False

# CORS Settings (if using frontend frameworks)
CORS_ALLOWED_ORIGINS = [
    "https://decipherworld-app.azurewebsites.net",
    "https://www.decipherworld.com",
    "https://decipherworld.com",
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
    try:
        db_config = DATABASES['default']
        logger.info(f"Azure PostgreSQL - HOST: {db_config.get('HOST')}, PORT: {db_config.get('PORT')}, NAME: {db_config.get('NAME')}")
    except Exception as e:
        logger.error(f"Database configuration logging error: {e}")