#!/usr/bin/env python
"""
Development server startup script for decipherworld
"""
import os
import sys
import subprocess

def run_server():
    """Start the Django development server"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.local')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    print("🚀 Starting Decipherworld local development server...")
    print("📝 Admin panel: http://127.0.0.1:8000/admin/")
    print("👤 Admin login: admin / admin123")
    print("🌐 Main site: http://127.0.0.1:8000/")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    execute_from_command_line(['manage.py', 'runserver'])

if __name__ == '__main__':
    run_server()