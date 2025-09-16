#!/usr/bin/env python3
"""
Simple URL testing script for DecipherWorld
Tests URLs using direct HTTP requests to localhost
Run this before every production deployment to ensure zero 500 errors
"""

import requests
import sys

def test_urls():
    """Test essential URLs for proper response codes and basic SEO"""
    base_url = 'http://127.0.0.1:8000'
    
    # Essential URLs to test
    urls_to_test = [
        # Core pages
        ('/', 200, "Homepage"),
        ('/courses/', 200, "Courses page"),
        ('/teachers/', 200, "Teachers page"),
        ('/schools/', 200, "Schools page"),
        ('/gallery/', 200, "Gallery page"),
        ('/contact/', 200, "Contact page"),
        
        # Games Hub
        ('/games/', 200, "Games Hub"),
        
        # Individual Games
        ('/games/ai-learning/', 200, "AI Learning Games"),
        ('/games/cyber-security/', 200, "Cyber Security Games"),
        ('/games/financial-literacy/', 200, "Financial Literacy Games"),
        
        # Team Games
        ('/games/constitution-basic/', 200, "Constitution Basic Games"),
        ('/games/constitution-advanced/', 200, "Constitution Advanced Games"),
        ('/games/entrepreneurship/', 200, "Entrepreneurship Games"),
        ('/games/group-learning/', 200, "Group Learning Games"),
        
        # Robotic Buddy
        ('/buddy/', 200, "Robotic Buddy Home"),
        ('/buddy/create-buddy/', 200, "Create Buddy"),
        ('/buddy/activities/', 200, "Buddy Activities"),
        
        # Group Learning
        ('/learn/', 200, "Group Learning Home"),
        ('/learn/game/1/', 200, "Game Detail Page (was 500)"),
        ('/learn/session/create/1/', 200, "Start Session (was 500)"),
        ('/learn/session/0DWOO2/reflection/', 200, "Reflection page (was 500)"),
        
        # System URLs
        ('/sitemap.xml', 200, "Sitemap"),
        ('/robots.txt', 200, "Robots.txt"),
        
        # Test 404 handling
        ('/nonexistent-page-test/', 404, "404 handling"),
    ]
    
    passed = 0
    failed = 0
    results = []
    
    print("🚀 Testing essential DecipherWorld URLs...")
    print("=" * 60)
    
    for url, expected_status, description in urls_to_test:
        try:
            full_url = base_url + url
            response = requests.get(full_url, timeout=10)
            status_code = response.status_code
            
            # Check basic SEO elements for 200 responses
            seo_info = ""
            if status_code == 200:
                content = response.text
                has_title = '<title>' in content and '</title>' in content
                has_meta_desc = 'name="description"' in content
                has_canonical = 'rel="canonical"' in content
                
                seo_warnings = []
                if not has_title:
                    seo_warnings.append("no title")
                if not has_meta_desc:
                    seo_warnings.append("no meta desc")
                if not has_canonical:
                    seo_warnings.append("no canonical")
                    
                if seo_warnings:
                    seo_info = f" ⚠️  {', '.join(seo_warnings)}"
            
            if status_code == expected_status:
                passed += 1
                print(f"✅ {url} - {status_code} - {description}{seo_info}")
            else:
                failed += 1
                print(f"❌ {url} - Expected {expected_status}, got {status_code} - {description}")
                
            results.append({
                'url': url,
                'status_code': status_code,
                'expected_status': expected_status,
                'success': status_code == expected_status,
                'description': description
            })
            
        except requests.exceptions.RequestException as e:
            failed += 1
            print(f"💥 {url} - Connection Error: {str(e)} - {description}")
            results.append({
                'url': url,
                'error': str(e),
                'success': False,
                'description': description
            })
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 URL TESTING REPORT")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🚀 DEPLOYMENT READINESS:")
        print("✅ READY FOR PRODUCTION - All essential URLs working!")
        return True
    else:
        print("\n🚀 DEPLOYMENT READINESS:")
        print("❌ NOT READY - Fix failing URLs before deploying to production")
        
        # Show failed URLs
        print("\n🔥 FAILED URLs:")
        for result in results:
            if not result.get('success', False):
                error_msg = result.get('error', f"Status {result.get('status_code', 'unknown')}")
                print(f"   - {result['url']}: {error_msg}")
        
        return False

def main():
    """Main function"""
    print("🔍 DecipherWorld URL Health Check")
    print("Make sure your local server is running on http://127.0.0.1:8000")
    print()
    
    # Check if server is running
    try:
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        print(f"✅ Server is running (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not accessible: {e}")
        print("Please run: python manage.py runserver 8000")
        return False
    
    print()
    ready_for_deployment = test_urls()
    
    # Exit with appropriate code for CI/CD
    sys.exit(0 if ready_for_deployment else 1)

if __name__ == '__main__':
    main()