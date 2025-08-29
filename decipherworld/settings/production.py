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
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

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
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
}