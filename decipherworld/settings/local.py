from .base import *
from decouple import config
import os

# Override base settings for local development
DEBUG = True
SECRET_KEY = 'django-insecure-local-development-key-only'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Use SQLite for local development (easier setup)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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