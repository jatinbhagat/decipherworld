#!/usr/bin/env python3
"""
Quick test script to verify learning module functionality
Run this while your Django server is running on another terminal
"""
import requests
import json

def test_learning_modules():
    base_url = "http://127.0.0.1:8000"
    session_code = "WL0BW0"  # The test session we created
    
    print("🧪 LEARNING MODULE DIAGNOSTIC TEST")
    print("=" * 50)
    
    # Test 1: Check if session exists
    print("1. Testing session access...")
    try:
        response = requests.get(f"{base_url}/learn/session/{session_code}/")
        if response.status_code == 200:
            print("✅ Session accessible")
        else:
            print(f"❌ Session not accessible: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Test 2: Check if learning modal HTML is present
    print("2. Checking for learning modal in HTML...")
    if 'learning-modal' in response.text:
        print("✅ Learning modal HTML found")
    else:
        print("❌ Learning modal HTML missing")
    
    # Test 3: Check if JavaScript functions are present
    print("3. Checking for learning module JavaScript...")
    if 'showLearningModule' in response.text:
        print("✅ Learning module JavaScript found")
    else:
        print("❌ Learning module JavaScript missing")
    
    # Test 4: Check leaderboard API (should work)
    print("4. Testing leaderboard API...")
    try:
        response = requests.get(f"{base_url}/learn/api/constitution/{session_code}/leaderboard/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Leaderboard API works ({data['total_teams']} teams)")
        else:
            print(f"❌ Leaderboard API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Leaderboard API error: {e}")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Go to: http://127.0.0.1:8000/learn/session/WL0BW0/")
    print("2. Create a team and start playing")
    print("3. Open browser DevTools (F12) to see console messages")
    print("4. Answer questions and watch for learning modules")
    print("\n📧 If issues persist, check:")
    print("- Browser console for JavaScript errors")
    print("- Django server logs for backend errors")
    print("- Database has learning modules (run the status check)")

if __name__ == "__main__":
    test_learning_modules()