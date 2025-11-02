#!/usr/bin/env python3
"""
Simple test for submission review workflow
"""

import os
import sys
import requests
import json

# Add Django project to path
sys.path.append('/Users/jatinbhagat/projects/decipherworld')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')

import django
django.setup()

from group_learning.models import DesignThinkingSession, DesignTeam, SimplifiedPhaseInput

def test_submission_workflow():
    """Test the complete submission workflow"""
    print("🧪 Testing Submission Review Workflow")
    
    # Find existing session
    session_code = "G03KHM"
    try:
        session = DesignThinkingSession.objects.get(session_code=session_code)
        print(f"✅ Found session: {session.session_code}")
        
        # Check existing teams
        teams = DesignTeam.objects.filter(session=session)
        print(f"✅ Found {teams.count()} teams")
        
        if teams.count() == 0:
            print("⚠️ No teams found - creating minimal test team")
            return False
        
        # Check existing submissions
        submissions = SimplifiedPhaseInput.objects.filter(team__session=session)
        print(f"✅ Found {submissions.count()} submissions")
        
        if submissions.count() == 0:
            print("⚠️ No submissions found - creating test submission")
            team = teams.first()
            SimplifiedPhaseInput.objects.create(
                team=team,
                mission='empathy_pain_points',
                student_name='Test Student',
                selected_value='Test submission for scoring workflow',
                input_label='Test Input'
            )
            print("✅ Created test submission")
        
        # Test the scoring API
        return test_scoring_api(session_code)
        
    except DesignThinkingSession.DoesNotExist:
        print(f"❌ Session {session_code} not found")
        return False

def test_scoring_api(session_code):
    """Test the scoring API endpoint"""
    print(f"\n🔧 Testing scoring API...")
    
    try:
        # Get teacher dashboard and extract CSRF token + submission ID
        session_req = requests.Session()
        dashboard_url = f"http://localhost:8001/learn/simplified/{session_code}/teacher/"
        resp = session_req.get(dashboard_url)
        
        if resp.status_code != 200:
            print(f"❌ Dashboard failed: {resp.status_code}")
            return False
            
        print(f"✅ Dashboard loaded: {len(resp.text)} bytes")
        
        # Quick check if submission review section exists
        if 'submission-review-container' in resp.text:
            print("✅ Submission review interface detected")
        else:
            print("⚠️ No submission review interface found")
            
        # Check if there are unscored submissions
        if 'data-submission-id=' in resp.text:
            print("✅ Unscored submissions found")
            
            # Extract submission ID
            start = resp.text.find('data-submission-id="') + 20
            end = resp.text.find('"', start)
            submission_id = resp.text[start:end]
            print(f"✅ Submission ID: {submission_id}")
            
            # Extract CSRF token
            csrf_start = resp.text.find('csrfmiddlewaretoken') 
            csrf_start = resp.text.find('value="', csrf_start) + 7
            csrf_end = resp.text.find('"', csrf_start)
            csrf_token = resp.text[csrf_start:csrf_end]
            print(f"✅ CSRF token: {csrf_token[:10]}...")
            
            # Test scoring API
            scoring_url = f"http://localhost:8001/learn/api/simplified/{session_code}/score-submission/"
            
            headers = {
                'X-CSRFToken': csrf_token,
                'Referer': dashboard_url
            }
            
            scoring_data = {
                'submission_id': submission_id,
                'score': '9'
            }
            
            score_resp = session_req.post(scoring_url, data=scoring_data, headers=headers)
            print(f"📊 Scoring response: {score_resp.status_code}")
            
            if score_resp.status_code == 200:
                try:
                    data = score_resp.json()
                    print(f"✅ Scoring successful: {data.get('success', False)}")
                    if data.get('success'):
                        print(f"✅ Progress: {data.get('scored_count', 0)}/{data.get('total_count', 0)} scored")
                        return True
                    else:
                        print(f"❌ Scoring failed: {data.get('message', 'Unknown error')}")
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON: {score_resp.text[:100]}")
            else:
                print(f"❌ API failed: {score_resp.text[:100]}")
                
        else:
            print("✅ All submissions already scored")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    return False

if __name__ == "__main__":
    success = test_submission_workflow()
    if success:
        print("\n🎉 Submission review workflow test PASSED!")
    else:
        print("\n❌ Submission review workflow test FAILED!")
    sys.exit(0 if success else 1)