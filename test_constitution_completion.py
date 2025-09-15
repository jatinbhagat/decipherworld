#!/usr/bin/env python3
"""
Test Constitution Challenge completion redirect behavior
"""
import requests
import re
import sys
from urllib.parse import urljoin

def test_constitution_completion():
    """Test the Constitution Challenge completion flow"""
    
    base_url = "https://decipherworld.com"
    stuck_url = "https://decipherworld.com/learn/constitution/SCD29Z/play/?team_id=17"
    
    print("🔍 Testing Constitution Challenge Completion Flow")
    print("=" * 60)
    
    # Test 1: Check if the stuck URL loads
    print(f"📍 Testing stuck URL: {stuck_url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    try:
        response = session.get(stuck_url, allow_redirects=True)
        print(f"   Status: {response.status_code}")
        print(f"   Final URL: {response.url}")
        
        if response.status_code == 200:
            # Check if this is the game page or results page
            if '/final-results/' in response.url:
                print("   ✅ Correctly redirected to results page!")
            elif '/play/' in response.url:
                print("   ⚠️ Still on play page - need to check JavaScript logic")
                
                # Look for the JavaScript completion logic in the response
                content = response.text
                
                # Check if our new completion logic is present
                if 'result.game_completed || (!result.next_question && !result.learning_module)' in content:
                    print("   ✅ Enhanced completion logic found in JavaScript")
                else:
                    print("   ❌ Enhanced completion logic not found - deployment may not be complete")
                
                # Check for CSRF token
                csrf_pattern = r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']'
                csrf_match = re.search(csrf_pattern, content)
                if csrf_match:
                    print("   ✅ CSRF token found")
                else:
                    print("   ⚠️ CSRF token not found")
                
                # Test the answer submission API to see game state
                api_url = f"{base_url}/learn/api/constitution/SCD29Z/submit-answer/?team_id=17"
                print(f"   📡 Testing API endpoint: {api_url}")
                
                # We can't actually submit without valid data, but we can check the endpoint exists
                api_response = session.get(api_url.replace('/submit-answer/', '/status/'))
                print(f"   API Status: {api_response.status_code}")
                
            else:
                print("   ❓ Unexpected page type")
        else:
            print(f"   ❌ Error: {response.status_code}")
            
    except requests.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    
    print("\n🔧 Recommendations:")
    print("1. Check if Azure deployment completed successfully")
    print("2. Verify JavaScript changes are live in browser dev tools") 
    print("3. Check team completion status in production database")
    print("4. Monitor browser console for completion detection logs")

if __name__ == "__main__":
    test_constitution_completion()