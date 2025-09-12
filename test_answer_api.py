#!/usr/bin/env python3
"""
Test the Constitution Answer API to see if learning modules are returned
"""
import requests
import json

def test_answer_api():
    print("🧪 TESTING CONSTITUTION ANSWER API")
    print("=" * 50)
    
    # Test data
    base_url = "http://127.0.0.1:8000"
    session_code = "WL0BW0"
    
    # First, get the team ID and first question
    print("1. Getting session data...")
    try:
        # Get CSRF token first
        session = requests.Session()
        csrf_response = session.get(f"{base_url}/learn/constitution/{session_code}/")
        
        if csrf_response.status_code != 200:
            print(f"❌ Could not access session page: {csrf_response.status_code}")
            return
            
        # Extract CSRF token
        csrf_token = None
        for line in csrf_response.text.split('\n'):
            if 'csrfmiddlewaretoken' in line and 'value=' in line:
                csrf_token = line.split('value="')[1].split('"')[0]
                break
        
        print(f"✅ Got CSRF token: {csrf_token[:10]}...")
        
        # Get team and question info from Django
        print("2. Getting test data from Django...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    print("\n📝 MANUAL TEST INSTRUCTIONS:")
    print("Since the API requires CSRF token and team context, please:")
    print("1. Open browser dev tools (F12)")
    print("2. Go to: http://127.0.0.1:8000/learn/constitution/WL0BW0/play/")
    print("3. Answer a question")
    print("4. Check console for:")
    print("   - '📚 Showing learning module: [title]' (success)")
    print("   - Any JavaScript errors")
    print("   - Network tab for API calls")

if __name__ == "__main__":
    test_answer_api()