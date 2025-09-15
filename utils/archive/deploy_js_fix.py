#!/usr/bin/env python3
"""
Deploy JavaScript fix to Azure and verify deployment
"""
import requests
import time
import re

def check_js_deployment():
    """Check if our JavaScript fix is deployed to production"""
    
    print("🚀 Checking JavaScript Fix Deployment")
    print("=" * 50)
    
    # Check the main Constitution Challenge page for our enhanced logic
    test_urls = [
        "https://decipherworld.com/learn/constitution/SCD29Z/play/?team_id=17",
        "https://decipherworld.com/static/js/constitution_challenge.js"
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{i}. Testing: {url}")
        
        try:
            response = session.get(url)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                
                # Check for our enhanced completion logic
                enhanced_logic = 'result.game_completed || (!result.next_question && !result.learning_module)'
                if enhanced_logic in content:
                    print("   ✅ Enhanced completion logic FOUND!")
                else:
                    print("   ❌ Enhanced completion logic NOT found")
                
                # Check for our new logging
                new_logging = '🎉 Game completed! Redirecting to results...'
                if new_logging in content:
                    print("   ✅ Enhanced logging FOUND!")
                else:
                    print("   ❌ Enhanced logging NOT found")
                
                # If this is the direct JS file, show a snippet
                if 'constitution_challenge.js' in url:
                    # Find the submitAnswer function
                    submit_pattern = r'function submitAnswer.*?(?=function|\Z)'
                    match = re.search(submit_pattern, content, re.DOTALL)
                    if match:
                        snippet = match.group(0)[:500] + "..."
                        print(f"   📄 JS Function snippet:\n   {snippet[:200]}...")
                    
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    print("\n🔄 Final Test - Checking the stuck URL behavior...")
    
    # Test the specific stuck URL
    stuck_url = "https://decipherworld.com/learn/constitution/SCD29Z/play/?team_id=17"
    try:
        response = session.get(stuck_url, allow_redirects=False)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 302 or response.status_code == 301:
            print(f"   ✅ REDIRECTING to: {response.headers.get('Location', 'Unknown')}")
        elif response.status_code == 200:
            if '/final-results/' in response.url:
                print("   ✅ Already on results page!")
            else:
                print("   ⚠️ Still on play page - JavaScript fix needed")
                # Check if page has the game complete state
                if 'game_completed":true' in response.text.lower():
                    print("   📊 Server indicates game is completed")
                else:
                    print("   📊 Server indicates game is NOT completed")
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Failed to test stuck URL: {e}")
    
    print("\n📋 Next Steps:")
    print("1. If enhanced logic not found, force static files collection")
    print("2. If found but not working, check team completion status in database")
    print("3. If team completed but not redirecting, debug JavaScript in browser")

if __name__ == "__main__":
    check_js_deployment()