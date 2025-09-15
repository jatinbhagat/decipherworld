#!/usr/bin/env python3
"""
Comprehensive URL testing script for DecipherWorld
Tests all URLs for proper HTTP status codes, SEO elements, and functionality
Run this before every production deployment to ensure zero 500 errors
"""

import os
import sys
import django
import requests
from urllib.parse import urljoin
from django.test.client import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')
django.setup()

from group_learning.models import Game, GameSession

class URLTester:
    def __init__(self, base_url='http://127.0.0.1:8000'):
        self.base_url = base_url
        self.client = Client()
        self.results = []
        self.errors = []
        self.passed = 0
        self.failed = 0
        
    def test_url(self, url, expected_status=200, description=""):
        """Test a single URL and return results"""
        try:
            full_url = urljoin(self.base_url, url)
            
            # Use Django test client for better error reporting
            response = self.client.get(url, follow=True)
            
            status_code = response.status_code
            content = response.content.decode('utf-8', errors='ignore')
            
            # Check for basic SEO elements
            has_title = '<title>' in content and '</title>' in content
            has_meta_desc = 'meta name="description"' in content
            has_canonical = 'rel="canonical"' in content
            has_og_tags = 'property="og:' in content
            
            result = {
                'url': url,
                'full_url': full_url,
                'status_code': status_code,
                'expected_status': expected_status,
                'description': description,
                'has_title': has_title,
                'has_meta_desc': has_meta_desc,
                'has_canonical': has_canonical,
                'has_og_tags': has_og_tags,
                'content_length': len(content),
                'success': status_code == expected_status
            }
            
            if status_code == expected_status:
                self.passed += 1
                print(f"✅ {url} - {status_code} - {description}")
            else:
                self.failed += 1
                print(f"❌ {url} - Expected {expected_status}, got {status_code} - {description}")
                
            # Check for SEO issues
            if status_code == 200:
                if not has_title:
                    print(f"   ⚠️  Missing title tag")
                if not has_meta_desc:
                    print(f"   ⚠️  Missing meta description")
                if not has_canonical:
                    print(f"   ⚠️  Missing canonical tag")
                    
            self.results.append(result)
            return result
            
        except Exception as e:
            self.failed += 1
            error = {
                'url': url,
                'error': str(e),
                'description': description
            }
            self.errors.append(error)
            print(f"💥 {url} - ERROR: {str(e)} - {description}")
            return error
    
    def run_all_tests(self):
        """Run comprehensive URL tests"""
        print("🚀 Starting comprehensive URL testing for DecipherWorld...")
        print("=" * 60)
        
        # Core URLs
        print("\n📍 Testing Core URLs:")
        self.test_url('/', 200, "Homepage")
        self.test_url('/courses/', 200, "Courses page")
        self.test_url('/teachers/', 200, "Teachers page")
        self.test_url('/schools/', 200, "Schools page")
        self.test_url('/gallery/', 200, "Gallery page")
        self.test_url('/contact/', 200, "Contact page")
        
        # Games URLs
        print("\n🎮 Testing Games URLs:")
        self.test_url('/games/', 200, "Games Hub")
        self.test_url('/games/ai-learning/', 200, "AI Learning Games")
        self.test_url('/games/group-learning/', 200, "Group Learning Games")
        self.test_url('/games/stem-challenges/', 200, "STEM Challenges")
        self.test_url('/games/language-adventures/', 200, "Language Adventures")
        
        # Robotic Buddy URLs
        print("\n🤖 Testing Robotic Buddy URLs:")
        self.test_url('/buddy/', 200, "Robotic Buddy Home")
        self.test_url('/buddy/create/', 200, "Create Buddy")
        self.test_url('/buddy/activities/', 200, "Buddy Activities")
        self.test_url('/buddy/simple-game/', 200, "Simple Game")
        self.test_url('/buddy/classification-game/', 200, "Classification Game")
        self.test_url('/buddy/drag-drop-game/', 200, "Drag Drop Game")
        self.test_url('/buddy/emotion-game/', 200, "Emotion Game")
        
        # Group Learning URLs
        print("\n👥 Testing Group Learning URLs:")
        self.test_url('/learn/', 200, "Group Learning Home")
        
        # Test with actual data if available
        try:
            games = Game.objects.filter(is_active=True)[:3]  # Test first 3 games
            for game in games:
                self.test_url(f'/learn/game/{game.id}/', 200, f"Game Detail: {game.title[:30]}...")
                self.test_url(f'/learn/session/create/{game.id}/', 200, f"Create Session: {game.title[:20]}...")
            
            # Test session URLs if sessions exist
            sessions = GameSession.objects.all()[:2]  # Test first 2 sessions
            for session in sessions:
                self.test_url(f'/learn/session/{session.session_code}/', 200, f"Session Detail: {session.session_code}")
                self.test_url(f'/learn/session/{session.session_code}/dashboard/', 200, f"Session Dashboard: {session.session_code}")
                self.test_url(f'/learn/play/{session.session_code}/', 200, f"Gameplay: {session.session_code}")
                self.test_url(f'/learn/session/{session.session_code}/results/', 200, f"Session Results: {session.session_code}")
                self.test_url(f'/learn/session/{session.session_code}/reflection/', 200, f"Reflection: {session.session_code}")
                
        except Exception as e:
            print(f"   ℹ️  Skipping dynamic URLs (no test data): {str(e)}")
        
        # API Endpoints
        print("\n🔌 Testing API Endpoints:")
        try:
            session = GameSession.objects.first()
            if session:
                self.test_url(f'/learn/api/session/{session.session_code}/status/', 200, "Session Status API")
                self.test_url(f'/learn/api/session/{session.session_code}/actions/', 200, "Session Actions API")
        except Exception as e:
            print(f"   ℹ️  Skipping API tests (no test data): {str(e)}")
        
        # Essential System URLs
        print("\n🛠️  Testing System URLs:")
        self.test_url('/sitemap.xml', 200, "Sitemap")
        self.test_url('/robots.txt', 200, "Robots.txt")
        
        # Test some expected 404s to ensure proper error handling
        print("\n❌ Testing 404 Handling:")
        self.test_url('/nonexistent-page/', 404, "Non-existent page (should be 404)")
        self.test_url('/learn/game/99999/', 404, "Non-existent game (should be 404)")
        self.test_url('/learn/session/INVALID/', 404, "Invalid session code (should be 404)")
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 URL TESTING REPORT")
        print("=" * 60)
        
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Total: {self.passed + self.failed}")
        print(f"📈 Success Rate: {(self.passed / (self.passed + self.failed)) * 100:.1f}%")
        
        # SEO Analysis
        seo_issues = []
        total_200_pages = 0
        pages_with_all_seo = 0
        
        for result in self.results:
            if isinstance(result, dict) and result.get('status_code') == 200:
                total_200_pages += 1
                has_all_seo = (result.get('has_title', False) and 
                              result.get('has_meta_desc', False) and 
                              result.get('has_canonical', False))
                if has_all_seo:
                    pages_with_all_seo += 1
                else:
                    seo_issues.append(result['url'])
        
        if total_200_pages > 0:
            print(f"\n🎯 SEO ANALYSIS:")
            print(f"Pages with complete SEO: {pages_with_all_seo}/{total_200_pages}")
            if seo_issues:
                print(f"Pages missing SEO elements:")
                for url in seo_issues[:5]:  # Show first 5
                    print(f"   - {url}")
        
        # Critical Errors
        if self.errors:
            print(f"\n💥 CRITICAL ERRORS:")
            for error in self.errors:
                print(f"   {error['url']}: {error['error']}")
        
        # Deployment Readiness
        print(f"\n🚀 DEPLOYMENT READINESS:")
        if self.failed == 0 and not self.errors:
            print("✅ READY FOR PRODUCTION - All tests passed!")
            return True
        else:
            print("❌ NOT READY - Fix issues before deploying to production")
            return False

def main():
    """Main function to run URL tests"""
    import argparse
    parser = argparse.ArgumentParser(description='Test all URLs for DecipherWorld')
    parser.add_argument('--url', default='http://127.0.0.1:8000', 
                       help='Base URL to test (default: http://127.0.0.1:8000)')
    args = parser.parse_args()
    
    tester = URLTester(args.url)
    ready_for_deployment = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if ready_for_deployment else 1)

if __name__ == '__main__':
    main()