#!/usr/bin/env python3
"""
Script to run in Azure SSH to collect static files
"""
import subprocess
import sys

def run_collectstatic():
    """Run collectstatic in Azure environment"""
    print("🔄 Running collectstatic in production environment...")
    
    try:
        # Run collectstatic with verbose output
        result = subprocess.run([
            'python', 'manage.py', 'collectstatic', 
            '--clear', '--noinput', '--verbosity=1'
        ], capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Static files collection completed successfully!")
        else:
            print(f"❌ Static files collection failed with code {result.returncode}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running collectstatic: {e}")
        return False

if __name__ == "__main__":
    success = run_collectstatic()
    sys.exit(0 if success else 1)