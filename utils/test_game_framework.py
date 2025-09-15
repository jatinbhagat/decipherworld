#!/usr/bin/env python3
"""
Game Framework Integration Test
Verifies that the new framework doesn't break existing functionality
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')
django.setup()

from games.compatibility import run_framework_integration_test


def main():
    """Run the framework integration test"""
    
    print("🚀 DecipherWorld Game Framework Integration Test")
    print("=" * 60)
    print()
    
    # Run the integration test
    try:
        test_data = run_framework_integration_test()
        
        # Print the report
        print(test_data['report'])
        
        # Return appropriate exit code
        exit_code = 0 if test_data['all_passed'] else 1
        
        if test_data['all_passed']:
            print("🎯 FRAMEWORK READY: All compatibility tests passed!")
            print("✅ Safe to deploy - no breaking changes detected")
        else:
            print("⚠️  FRAMEWORK ISSUES: Some tests failed")
            print("❌ Review and fix issues before deployment")
        
        return exit_code
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)