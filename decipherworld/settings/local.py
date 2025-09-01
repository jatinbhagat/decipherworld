from .base import *
from decouple import config
import os

# Override base settings for local development
DEBUG = True
SECRET_KEY = 'django-insecure-local-development-key-only'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database configuration - Force Supabase PostgreSQL with robust error handling
import dj_database_url
import os

def get_database_config():
    """Get database configuration with proper URL encoding support"""
    
    # Try multiple ways to get DATABASE_URL
    database_url = None
    
    # Method 1: python-decouple
    try:
        database_url = config('DATABASE_URL', default='')
        if database_url:
            print(f"✅ Got DATABASE_URL from decouple: {len(database_url)} chars")
    except Exception as e:
        print(f"⚠️  Decouple failed: {e}")
    
    # Method 2: Direct environment variable
    if not database_url:
        database_url = os.environ.get('DATABASE_URL', '')
        if database_url:
            print(f"✅ Got DATABASE_URL from os.environ: {len(database_url)} chars")
    
    # Method 3: Force hardcoded Supabase config (for debugging)
    if not database_url or database_url.startswith('postgresql://postgres.[your-'):
        print("🔧 Using hardcoded Supabase configuration")
        return {
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
    
    # Parse the DATABASE_URL
    try:
        parsed_db = dj_database_url.parse(
            database_url,
            conn_max_age=600,
            ssl_require=True
        )
        
        # Ensure NAME is set
        if not parsed_db.get('NAME'):
            parsed_db['NAME'] = 'postgres'
            
        # Force TCP connection (never use sockets) 
        if not parsed_db.get('HOST') or parsed_db.get('HOST') in ['localhost', '127.0.0.1', '']:
            print(f"❌ Invalid host detected: {parsed_db.get('HOST')}")
            raise ValueError("Invalid host - would use socket connection")
        
        # Force PORT to be set (never use default socket)
        if not parsed_db.get('PORT'):
            print("❌ No PORT specified - could default to socket")
            raise ValueError("No PORT specified - would use socket connection")
            
        # Ensure we have all required connection parameters
        required_fields = ['ENGINE', 'NAME', 'USER', 'PASSWORD', 'HOST', 'PORT']
        for field in required_fields:
            if not parsed_db.get(field):
                print(f"❌ Missing required field: {field}")
                raise ValueError(f"Missing required database field: {field}")
                
        print(f"✅ Parsed DATABASE_URL successfully")
        print(f"🔌 Will connect to: {parsed_db['HOST']}:{parsed_db['PORT']}")
        return parsed_db
        
    except Exception as e:
        print(f"❌ Failed to parse DATABASE_URL: {e}")
        print("🔧 Falling back to hardcoded Supabase config")
        return {
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

# Get database configuration
try:
    db_config = get_database_config()
    DATABASES = {
        'default': db_config
    }
    print("✅ Using Supabase PostgreSQL for local development")
    print(f"🔌 Connecting to: {db_config['HOST']}:{db_config['PORT']}")
    
except Exception as e:
    print(f"❌ Database configuration failed: {e}")
    print("📋 Falling back to SQLite")
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