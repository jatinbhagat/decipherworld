from .base import *
from decouple import config
import os

# Override base settings for local development
DEBUG = True
SECRET_KEY = 'django-insecure-local-development-key-only'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database configuration - Try Supabase first, fallback to SQLite
import dj_database_url

# Try to use DATABASE_URL first (Supabase PostgreSQL)
DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL and not DATABASE_URL.startswith('postgresql://postgres.[your-'):
    # Valid Supabase URL provided
    try:
        # Manual parsing for Supabase URLs with special characters in password
        if 'aws-1-ap-south-1.pooler.supabase.com' in DATABASE_URL:
            # Direct Supabase configuration for your specific setup
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': 'postgres',
                    'USER': 'postgres.tpgymvjnrmugrjfjwtbb',
                    'PASSWORD': 'OmNamoShivaay@#7',
                    'HOST': 'aws-1-ap-south-1.pooler.supabase.com',
                    'PORT': '6543',
                    'OPTIONS': {
                        'sslmode': 'require',
                        'connect_timeout': 60,
                        'application_name': 'django_decipherworld',
                    },
                    'CONN_MAX_AGE': 600,
                }
            }
        else:
            # Try dj_database_url for other formats
            parsed_db = dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=600,
                ssl_require=True
            )
            
            # Ensure NAME is set properly
            if not parsed_db.get('NAME'):
                parsed_db['NAME'] = 'postgres'
            
            DATABASES = {
                'default': parsed_db
            }
        
        print("✅ Using Supabase PostgreSQL for local development")
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
        print("📋 Falling back to SQLite - see SETUP_SUPABASE.md for setup instructions")
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
else:
    # No valid DATABASE_URL - use SQLite temporarily
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    if not DATABASE_URL:
        print("📋 Using SQLite temporarily - add DATABASE_URL to .env for Supabase PostgreSQL")
    else:
        print("📋 DATABASE_URL contains placeholders - using SQLite until real credentials are added")

# For Supabase integration (optional in local dev)
SUPABASE_URL = config('SUPABASE_URL', default='')
SUPABASE_KEY = config('SUPABASE_ANON_KEY', default='')
SUPABASE_SERVICE_KEY = config('SUPABASE_SERVICE_KEY', default='')

# Static Files (development)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media Files (development)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email backend for development (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable HTTPS redirect for local development
SECURE_SSL_REDIRECT = False

# CORS settings for local development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Development toolbar (optional)
# Uncomment these lines if you want to use django-debug-toolbar
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']

# Logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
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
        'core': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}