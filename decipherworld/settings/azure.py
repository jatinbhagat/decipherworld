"""
Azure-specific Django settings for decipherworld project.
Optimized for Azure App Service and Azure PostgreSQL.
"""

from .base import *
from decouple import config
import os

# Override base settings for Azure production
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-temp-key-change-in-production')

# Azure App Service domains
ALLOWED_HOSTS = [
    'decipherworld-app.azurewebsites.net',  # Default Azure domain
    'www.decipherworld.com',                # Custom domain (if configured)
    'decipherworld.com',                    # Custom domain (if configured) 
    '.azurewebsites.net',                   # Allow all Azure App Service domains
]

# Azure PostgreSQL Database Configuration
import dj_database_url

def get_azure_database_config():
    """Get Azure PostgreSQL database configuration with robust error handling"""
    
    database_url = config('DATABASE_URL', default=None)
    
    if database_url:
        try:
            print(f"🔍 Parsing Azure DATABASE_URL (length: {len(database_url)} chars)")
            
            # Parse Azure PostgreSQL URL
            parsed_db = dj_database_url.parse(database_url, conn_max_age=600, ssl_require=True)
            
            print(f"🔍 Parsed Azure database config: {parsed_db}")
            
            # Ensure NAME is set properly
            if not parsed_db.get('NAME'):
                parsed_db['NAME'] = 'decipherworld'
                print("🔧 Set database NAME to 'decipherworld'")
            
            # Validate Azure PostgreSQL connection parameters
            host = parsed_db.get('HOST', '')
            port = parsed_db.get('PORT')
            user = parsed_db.get('USER', '')
            password = parsed_db.get('PASSWORD', '')
            
            print(f"🔍 Azure DB - HOST: '{host}', PORT: '{port}', USER: '{user}', PASSWORD: {'***' if password else 'MISSING'}")
            
            # Ensure all required fields are present
            if not host or not user or not password:
                raise ValueError("Missing required Azure database connection parameters")
            
            # Azure PostgreSQL specific options
            if 'OPTIONS' not in parsed_db:
                parsed_db['OPTIONS'] = {}
            
            parsed_db['OPTIONS'].update({
                'sslmode': 'require',           # Required for Azure PostgreSQL
                'connect_timeout': 60,
                'application_name': 'decipherworld_django',
            })
            
            print(f"✅ Azure database config ready - HOST: {parsed_db['HOST']}, PORT: {parsed_db.get('PORT', 5432)}")
            return parsed_db
            
        except Exception as e:
            print(f"❌ Error parsing Azure DATABASE_URL: {e}")
            raise e
    
    else:
        # Fallback to individual environment variables for Azure
        print("🔧 Using individual Azure database environment variables")
        
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='decipherworld'),
            'USER': config('DB_USER', default='decipheradmin'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='decipherworld-db-server.postgres.database.azure.com'),
            'PORT': config('DB_PORT', default='5432'),
            'OPTIONS': {
                'sslmode': 'require',
                'connect_timeout': 60,
                'application_name': 'decipherworld_django',
            },
            'CONN_MAX_AGE': 600,
        }

# Configure Azure database
try:
    azure_db_config = get_azure_database_config()
    DATABASES = {
        'default': azure_db_config
    }
    print("✅ Azure PostgreSQL configured successfully")
    
except Exception as db_error:
    print(f"❌ Azure database configuration failed: {db_error}")
    # This will cause deployment to fail, which is what we want
    raise db_error

# Azure Blob Storage for Static Files (Optional - can use WhiteNoise instead)
USE_AZURE_STORAGE = config('USE_AZURE_STORAGE', default=False, cast=bool)

if USE_AZURE_STORAGE:
    # Azure Storage Account configuration
    AZURE_ACCOUNT_NAME = config('AZURE_ACCOUNT_NAME')
    AZURE_ACCOUNT_KEY = config('AZURE_ACCOUNT_KEY') 
    AZURE_CONTAINER = config('AZURE_CONTAINER', default='static')
    
    # Django-storages configuration for Azure
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    STATICFILES_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    
    AZURE_LOCATION = 'static'
    STATIC_URL = f'https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER}/{AZURE_LOCATION}/'
else:
    # Use WhiteNoise for static files (simpler, recommended for small apps)
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    STATICFILES_DIRS = [
        BASE_DIR / 'static',
    ]
    
    # WhiteNoise middleware (already in base.py MIDDLEWARE)
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Azure App Service Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Additional Security Settings for Azure
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure Cookies for Azure HTTPS
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Azure App Service allows these headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# CORS Settings (if needed for API access)
CORS_ALLOWED_ORIGINS = [
    "https://decipherworld-app.azurewebsites.net",
    "https://www.decipherworld.com",
    "https://decipherworld.com",
]

# Azure Application Insights (Optional)
AZURE_APPINSIGHTS_KEY = config('AZURE_APPINSIGHTS_KEY', default='')
if AZURE_APPINSIGHTS_KEY:
    INSTALLED_APPS += ['applicationinsights.django']
    APPLICATION_INSIGHTS = {
        'ikey': AZURE_APPINSIGHTS_KEY,
    }

# Azure-optimized Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/tmp/django.log',  # Azure App Service tmp directory
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'azure': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Azure-specific email configuration (if using Azure Communication Services)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

if config('AZURE_COMMUNICATION_CONNECTION_STRING', default=''):
    # Configure Azure Communication Services for email
    AZURE_COMMUNICATION_CONNECTION_STRING = config('AZURE_COMMUNICATION_CONNECTION_STRING')

# Debug database connection in Azure logs
if not DEBUG:
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        db_config = DATABASES['default']
        logger.info(f"Azure Database configured - HOST: {db_config['HOST']}, NAME: {db_config['NAME']}")
    except Exception as log_error:
        logger.error(f"Failed to log Azure database config: {log_error}")

print("🚀 Azure Django settings loaded successfully!")