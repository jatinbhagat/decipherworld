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
    try:
        print(f"🔍 Parsing DATABASE_URL (length: {len(DATABASE_URL)} chars)")
        
        # First try dj_database_url parsing
        parsed_db = dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
        
        print(f"🔍 Parsed database config: {parsed_db}")
        
        # Ensure NAME is set properly
        if not parsed_db.get('NAME'):
            parsed_db['NAME'] = 'postgres'
            print("🔧 Set database NAME to 'postgres'")
        
        # Check for missing or invalid fields
        host = parsed_db.get('HOST', '')
        port = parsed_db.get('PORT')
        user = parsed_db.get('USER', '')
        password = parsed_db.get('PASSWORD', '')
        
        print(f"🔍 HOST: '{host}', PORT: '{port}', USER: '{user}', PASSWORD: {'***' if password else 'MISSING'}")
        
        # Force TCP connection (never use sockets)
        if not host or host in ['localhost', '127.0.0.1', '']:
            print(f"❌ Invalid host detected: '{host}' - forcing to Supabase host")
            parsed_db['HOST'] = 'aws-1-ap-south-1.pooler.supabase.com'
        
        # Force PORT to be set
        if not port:
            print("❌ No PORT specified - setting to 6543")
            parsed_db['PORT'] = 6543
        
        # Ensure USER is set
        if not user:
            print("❌ No USER specified - setting to default")
            parsed_db['USER'] = 'postgres.tpgymvjnrmugrjfjwtbb'
            
        # Ensure PASSWORD is set
        if not password:
            print("❌ No PASSWORD specified - this will cause connection failure")
            parsed_db['PASSWORD'] = config('DATABASE_PASSWORD', default='OmNamoShivaay@#7')
        
        # Add required OPTIONS if not present
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
        
        print(f"✅ Final database config - HOST: {DATABASES['default']['HOST']}, PORT: {DATABASES['default']['PORT']}")
        
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
        print(f"🔍 DATABASE_URL value: {DATABASE_URL[:50]}...")
        
        # Robust fallback configuration
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'postgres',
                'USER': config('DATABASE_USER', default='postgres.tpgymvjnrmugrjfjwtbb'),
                'PASSWORD': config('DATABASE_PASSWORD', default='OmNamoShivaay@#7'),
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
        print("🔧 Using robust fallback database configuration")
        
elif DIRECT_URL:
    try:
        # Use direct connection (port 5432)
        parsed_db = dj_database_url.parse(DIRECT_URL, conn_max_age=600, ssl_require=True)
        if not parsed_db.get('NAME'):
            parsed_db['NAME'] = 'postgres'
            
        DATABASES = {
            'default': parsed_db
        }
        print("Using Supabase direct connection (port 5432)")
        
    except Exception as e:
        print(f"Error parsing DIRECT_URL: {e}")
        # Fallback configuration
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'postgres',
                'USER': config('DATABASE_USER', default='postgres.tpgymvjnrmugrjfjwtbb'),
                'PASSWORD': config('DATABASE_PASSWORD'),
                'HOST': 'aws-1-ap-south-1.pooler.supabase.com',
                'PORT': 5432,
                'OPTIONS': {
                    'sslmode': 'require',
                    'connect_timeout': 60,
                    'application_name': 'django_decipherworld',
                },
                'CONN_MAX_AGE': 600,
            }
        }
        print("Using fallback direct database configuration")
    
else:
    # Final fallback - use environment variables or hardcoded Supabase config
    print("❌ No DATABASE_URL or DIRECT_URL found - using individual environment variables")
    
    try:
        db_host = config('DB_HOST', default='aws-1-ap-south-1.pooler.supabase.com')
        db_port = config('DB_PORT', default='6543')
        db_user = config('DB_USER', default='postgres.tpgymvjnrmugrjfjwtbb') 
        db_password = config('DB_PASSWORD', default='OmNamoShivaay@#7')
        db_name = config('DB_NAME', default='postgres')
        
        print(f"🔍 Individual env vars - HOST: {db_host}, PORT: {db_port}, USER: {db_user}")
        
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': db_name,
                'USER': db_user,
                'PASSWORD': db_password,
                'HOST': db_host,
                'PORT': db_port,
                'OPTIONS': {
                    'sslmode': 'require',
                    'connect_timeout': 60,
                    'application_name': 'django_decipherworld',
                },
                'CONN_MAX_AGE': 600,
            }
        }
        print(f"✅ Using individual env var connection to {db_host}:{db_port}")
        
    except Exception as env_error:
        print(f"❌ Environment variable error: {env_error}")
        
        # Ultimate fallback - hardcoded reliable configuration
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
        print("🔧 Using ultimate hardcoded fallback configuration")

# Supabase Configuration (optional - only needed if using Supabase auth features)
try:
    SUPABASE_URL = config('SUPABASE_URL')
    SUPABASE_KEY = config('SUPABASE_ANON_KEY') 
    SUPABASE_SERVICE_KEY = config('SUPABASE_SERVICE_KEY', default='')
    print(f"✅ Supabase configuration loaded: {SUPABASE_URL}")
except Exception as supabase_error:
    print(f"⚠️  Supabase config missing (optional): {supabase_error}")
    SUPABASE_URL = ''
    SUPABASE_KEY = ''
    SUPABASE_SERVICE_KEY = ''

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
    if DATABASE_URL:
        logger.info(f"Using DATABASE_URL for database connection")
    elif DIRECT_URL:
        logger.info(f"Using DIRECT_URL for database connection")
    else:
        try:
            logger.info(f"Database config - HOST: {get_db_host()}, NAME: {config('DB_NAME', default='postgres')}, USER: {config('DB_USER', default='N/A')}, PORT: {config('DB_PORT', default='5432')}")
        except:
            logger.info("Using fallback database configuration")