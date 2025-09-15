#!/usr/bin/env python3
"""
Debug script to test leaderboard functionality
"""
import requests

def debug_leaderboard():
    print("🔍 LEADERBOARD DEBUG TEST")
    print("=" * 50)
    
    session_code = "M2VDH7"
    base_url = "http://127.0.0.1:8000"
    
    # Test 1: Check if gameplay page loads
    print("1. Testing gameplay page...")
    try:
        response = requests.get(f"{base_url}/learn/constitution/{session_code}/play/")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            # Check for leaderboard elements
            html = response.text
            has_leaderboard_button = 'onclick="toggleLeaderboard()"' in html
            has_leaderboard_panel = 'id="leaderboard-panel"' in html  
            has_leaderboard_js = 'function toggleLeaderboard' in html
            
            print(f"   Has leaderboard button: {has_leaderboard_button}")
            print(f"   Has leaderboard panel: {has_leaderboard_panel}")
            print(f"   Has leaderboard JS: {has_leaderboard_js}")
            
            if has_leaderboard_button:
                # Count how many leaderboard buttons
                button_count = html.count('onclick="toggleLeaderboard()"')
                print(f"   Number of leaderboard buttons: {button_count}")
        else:
            print(f"   ❌ Page failed to load: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Test leaderboard API directly
    print("\n2. Testing leaderboard API...")
    try:
        response = requests.get(f"{base_url}/learn/api/constitution/{session_code}/leaderboard/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API works - {data['total_teams']} teams")
            for team in data['leaderboard'][:2]:
                print(f"      {team['rank']}. {team['team_name']} - {team['score']} points")
        else:
            print(f"   ❌ API failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API error: {e}")
    
    print("\n🎯 INSTRUCTIONS:")
    print("If the page loads but leaderboard doesn't work:")
    print("1. Press F12 in browser")
    print("2. Go to Console tab") 
    print("3. Click the leaderboard button")
    print("4. Look for debug messages starting with '🔍 LEADERBOARD DEBUG'")
    print("5. Report any error messages you see")

if __name__ == "__main__":
    debug_leaderboard()