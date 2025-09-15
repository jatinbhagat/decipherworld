#!/usr/bin/env python3
"""
Check and fix team completion status for Constitution Challenge
"""
import requests
import json
import re

def check_team_status():
    """Check the team completion status and game state"""
    
    print("🔍 Checking Team Completion Status")
    print("=" * 50)
    
    base_url = "https://decipherworld.com"
    session_code = "SCD29Z"
    team_id = "17"
    
    play_url = f"{base_url}/learn/constitution/{session_code}/play/?team_id={team_id}"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    print(f"📍 Testing play URL: {play_url}")
    
    # Get the play page to extract CSRF token and current game state
    try:
        response = session.get(play_url)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Extract CSRF token
            csrf_pattern = r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']'
            csrf_match = re.search(csrf_pattern, content)
            csrf_token = csrf_match.group(1) if csrf_match else None
            
            if csrf_token:
                print(f"   ✅ CSRF token extracted: {csrf_token[:10]}...")
            else:
                print("   ❌ CSRF token not found")
                return
            
            # Check current question state
            question_pattern = r'"current_question":\s*(\d+|null)'
            question_match = re.search(question_pattern, content)
            current_question = question_match.group(1) if question_match else "unknown"
            print(f"   📊 Current question: {current_question}")
            
            # Check total questions
            total_pattern = r'"total_questions":\s*(\d+)'
            total_match = re.search(total_pattern, content)
            total_questions = total_match.group(1) if total_match else "unknown"
            print(f"   📊 Total questions: {total_questions}")
            
            # Check completion status
            completed_pattern = r'"is_completed":\s*(true|false)'
            completed_match = re.search(completed_pattern, content)
            is_completed = completed_match.group(1) if completed_match else "unknown"
            print(f"   📊 Is completed: {is_completed}")
            
            # If not completed but we're at the end, try to trigger completion
            if is_completed == "false" and current_question == "null":
                print("\n🔧 Team not marked complete but no more questions - investigating...")
                
                # Try to get the answer submission API to understand the state
                api_url = f"{base_url}/learn/api/constitution/{session_code}/submit-answer/"
                headers = {
                    'X-CSRFToken': csrf_token,
                    'Content-Type': 'application/json',
                    'Referer': play_url
                }
                
                # We can't submit a real answer without knowing the question,
                # but we can check if the API gives us information
                print(f"   📡 Checking API state...")
                
                # Instead, let's try to reload the page to see if server-side redirect kicks in
                print("   🔄 Reloading page to check server-side redirect...")
                reload_response = session.get(play_url, allow_redirects=True)
                
                if reload_response.url != play_url:
                    print(f"   ✅ Server redirected to: {reload_response.url}")
                else:
                    print("   ⚠️ Server did not redirect - team may need manual completion")
            
            elif is_completed == "true":
                print("   ✅ Team is marked as completed - should redirect")
                
            else:
                print(f"   📝 Game in progress: {current_question}/{total_questions}")
                
        else:
            print(f"   ❌ Failed to load page: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error checking team status: {e}")
    
    print("\n📋 Summary:")
    print("- JavaScript fix is deployed to static files ✅")
    print("- Need to verify if team completion status is correct")
    print("- May need database intervention for stuck team")

if __name__ == "__main__":
    check_team_status()